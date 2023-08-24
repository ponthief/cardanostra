"""
    EventHandlers for Client subscribe method, there should be a do_event(evt, relay) which should be passed as the
    handler arg when calling the subscribe method. Eventually support mutiple handlers per sub and add.remove handlers
    plus maybe chain of handlers

"""
from __future__ import annotations
import hashlib
import inspect
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .ident.event_handlers import ProfileEventHandlerInterface
    from .client.client import Client
import asyncio
from datetime import datetime
from .ident.profile import ProfileList, Profile, Contact, ContactList
from abc import ABC, abstractmethod
import base64
import logging
import json
from collections import OrderedDict
from threading import BoundedSemaphore
from .encrypt import SharedEncrypt
from .util import util_funcs
from .event import Event


class EventAccepter(ABC):

    @abstractmethod
    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        'True/False if the event will be accepted'


class DeduplicateAcceptor(EventAccepter):

    def __init__(self, max_dedup=10000):
        # de-duplicating of events for when we're connected to multiple relays
        self._duplicates = OrderedDict()
        self._max_dedup = max_dedup

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        ret = False
        if evt.id not in self._duplicates:
            self._duplicates[evt.id] = True
            if len(self._duplicates) >= self._max_dedup:
                self._duplicates.popitem(last=False)
            ret = True
        return ret


class FilterAcceptor(EventAccepter):
    """
        Use this to make sure that relay is returning you the events that you requested.
        if the_filter is None then it'll always return True until the_filter is set
    """

    def __init__(self, the_filter=None):
        self._filter = the_filter

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, the_filter):
        self._filter = the_filter

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        ret = True
        if self._filter:
            ret = evt.test(self._filter)

        return ret


class DuplicateContentAcceptor(EventAccepter):
    def __init__(self, max_dedup=10000):
        # de-duplicating of events for when we're connected to multiple relays
        self._duplicates = OrderedDict()
        self._max_dedup = max_dedup

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        ret = False
        key = hashlib.md5(evt.content.encode('utf8')).hexdigest()
        logging.debug(key)
        if key not in self._duplicates:
            self._duplicates[key] = True
            if len(self._duplicates) >= self._max_dedup:
                self._duplicates.popitem(last=False)
            ret = True
        return ret


class NotOnlyNumbersAcceptor(EventAccepter):

    def __init__(self):
        pass

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        return not evt.content.replace(' ','').isdigit()


class LengthAcceptor(EventAccepter):

    def __init__(self, min=1, max=None):
        self._min = min
        self._max = max

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        ret = True
        msg_len = len(evt.content)
        if self._min and msg_len < self._min:
            ret = False
        if self._max and msg_len > self._max:
            ret = False
        return ret


class EventHandler(ABC):

    def __init__(self, event_acceptors: [EventAccepter] = []):
        if not hasattr(event_acceptors, '__iter__'):
            event_acceptors = [event_acceptors]
        self._event_acceptors = event_acceptors

    def accept_event(self,
                     the_client: Client,
                     sub_id: str,
                     evt: Event) -> bool:
        ret = True
        for accept in self._event_acceptors:
            if not accept.accept_event(the_client, sub_id, evt):
                ret = False
                break

        return ret

    @abstractmethod
    def do_event(self, the_client: Client, sub_id, evt: Event):
        """
        if not self.accept_event(the_client, sub_id, evt):
            do_something
        or just do_something if no accept criteria
        """


class PrintEventHandler(EventHandler):
    """
       basic handler for outputting events
    """
    def __init__(self,
                 event_acceptors=[],
                 view_on=True,
                 profile_handler: ProfileEventHandlerInterface = None,
                 max_length: int = None):

        self._view_on = view_on
        self._profile_handler = profile_handler
        self._max_length = max_length
        super().__init__(event_acceptors)

    def view_on(self):
        self._view_on = True

    def view_off(self):
        self._view_on = False

    def do_event(self, the_client: Client, sub_id, evt: Event):
        if not self.accept_event(the_client, sub_id, evt):
            return

        if self._view_on:
            asyncio.create_task(self.display_func(the_client, sub_id, evt))

    async def display_func(self, the_client: Client, sub_id, evt: Event):
        c_evt: Event
        if isinstance(evt, Event):
            evt = [evt]

        # if profile handler prefetch profiles
        if self._profile_handler is not None:
            if inspect.iscoroutinefunction(self._profile_handler.get_profiles):
                await self._profile_handler.get_profiles(pub_ks=[c_evt.pub_key for c_evt in evt],
                                                         create_missing=True)
            else:
                self._profile_handler.get_profiles(pub_ks=[c_evt.pub_key for c_evt in evt],
                                                   create_missing=True)

        for c_evt in evt:
            profile_name = c_evt.pub_key
            if self._profile_handler:
                if inspect.iscoroutinefunction(self._profile_handler.get_profile):
                    p: Profile = await self._profile_handler.get_profile(c_evt.pub_key)
                else:
                    p: Profile = self._profile_handler.get_profile(c_evt.pub_key)

                profile_name = p.display_name()

            content = c_evt.content
            if self._max_length and len(content) > self._max_length:
                content = content[:self._max_length-3]+ '...'

            print('%s: %s - %s' % (c_evt.created_at,
                                   util_funcs.str_tails(profile_name, 4),
                                   content))


class LastEventHandler(EventHandler):
    """
        use to keep track of the last time we received events for a given relay
    """
    def __init__(self):
        self._url_time_map = {}

    def do_event(self, the_client: Client, sub_id, evt: Event):
        self.set_now(the_client)

    def set_now(self, the_client):
        url = self._client_url(the_client)
        self._url_time_map[url] = datetime.now()

    @staticmethod
    def _client_url(the_client) -> str:
        ret = the_client
        if not isinstance(the_client, str):
            ret = the_client.url
        return ret

    def get_last_event_dt(self, the_client: Client) -> datetime:
        ret = None
        url = self._client_url(the_client)
        if url in self._url_time_map:
            ret = self._url_time_map[url]
        return ret

    def set_last_event_dt(self, the_client: Client, dt: datetime):
        self._url_time_map[self._client_url(the_client)] = dt


class DecryptPrintEventHandler(PrintEventHandler):
    """
        prints out decrypted messages we created or sent to us
        NOTE: this is not the style that is compatiable with clust, that uses a public inbox
        and encrypts the event as a package... want to add this too
    """

    def __init__(self, priv_k, view_on=True):
        self._priv_k = priv_k
        self._my_encrypt = SharedEncrypt(priv_k)
        super(DecryptPrintEventHandler, self).__init__(view_on)

    def _do_dycrypt(self, crypt_text, pub_key):
        msg_split = crypt_text.split('?iv')
        text = base64.b64decode(msg_split[0])
        iv = base64.b64decode(msg_split[1])

        return (self._my_encrypt.decrypt_message(encrypted_data=text,
                                                 iv=iv,
                                                 # note the ext is ignored anyway
                                                 pub_key_hex='02' + pub_key))

    def do_event(self, the_client: Client, sub_id, evt: Event):
        if self._view_on is False:
            return
        do_decrypt = False
        to_key = evt['tags'][0][1]
        print(to_key, self._my_encrypt.public_key_hex)
        if evt['kind'] == Event.KIND_ENCRYPT:
            # messages we created
            if evt['pubkey'] == self._my_encrypt.public_key_hex[2:]:
                pub_key = to_key
                do_decrypt = True

            # messages sent to us
            elif to_key == self._my_encrypt.public_key_hex[2:]:
                pub_key = evt['pubkey']
                do_decrypt = True

        content = evt['content']
        if do_decrypt:
            content = self._do_dycrypt(evt['content'], pub_key)

        print('%s: %s - %s' % (util_funcs.ticks_as_date(evt['created_at']),
                               evt['pubkey'],
                               content))


class FileEventHandler:

    def __init__(self, file_name, delete_exist=True):
        self._file_name = file_name
        if delete_exist:
            with open(self._file_name, 'w'):
                pass

    def do_event(self, the_client: Client, sub_id, evt: Event):
        # appends to
        with open(self._file_name, "a") as f:
            evt['pubkey'] = evt['pubkey']
            f.writelines(json.dumps(evt) + '\n')
        logging.debug('FileEventHandler::do_event event appended to file %s' % self._file_name)


# class EventTimeHandler:
#
#     def __init__(self, callback=None):
#         self._callback = callback
#
#     def do_event(self, the_client: Client, sub_id, evt: Event):
#         self._callback(evt['created_at'])


class RepostEventHandler:
    """
    reposts events seen  on to given Client/ClientPool object
    event size number of event ids to keep to prevent duplicates being sent out
    NOTE though this is really just to prevent wasteful repost of events, relays
    shouldn't have a problem receiving duplicate ids

    to_client, TODO: define interface that both Client and ClientPool share and type hint with that

    """
    def __init__(self, to_client, max_dedup=1000):
        self._to_client = to_client
        self._duplicates = OrderedDict()
        self._max_dedup = max_dedup
        self._lock = BoundedSemaphore()

    def do_event(self, the_client: Client, sub_id, evt: Event):
        do_send = False
        with self._lock:
            if evt.id not in self._duplicates:
                do_send = True
                self._duplicates[evt.id] = True
                if len(self._duplicates) >= self._max_dedup:
                    self._duplicates.popitem(False)

        if do_send:
            self._to_client.publish(evt)
            print('RepostEventHandler::sent event %s to %s' % (evt, self._to_client))
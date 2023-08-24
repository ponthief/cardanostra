import logging
import asyncio
from datetime import datetime
from lnbits.extensions.nostrboltcardbot.monstr.client.client import Client, ClientPool
from lnbits.extensions.nostrboltcardbot.monstr.event_handlers import EventHandler, DeduplicateAcceptor, LastEventHandler
from lnbits.extensions.nostrboltcardbot.monstr.event import Event
from lnbits.extensions.nostrboltcardbot.monstr.encrypt import Keys
from lnbits.extensions.nostrboltcardbot.monstr.util import util_funcs
from typing import Optional
from loguru import logger
import httpx

from lnbits.core import get_user
from lnbits.settings import settings

from . import nostrboltcardbot_ext
from lnbits.extensions.nostrboltcardbot.crud import get_all_nostrboltbot_settings
from lnbits.extensions.nostrboltcardbot.models import BotSettings

http_client: Optional[httpx.AsyncClient] = None
#DEFAULT_RELAY = 'wss://nostr-pub.wellorder.net,wss://nos.lol'
# DEFAULT_RELAY = 'ws://localhost:8888'
DEFAULT_RELAY = 'wss://nos.lol'
# bot account priv_k - to remove hardcode
USE_KEY = ''
#clients: dict[str, LnbitsClient] = {}


def get_args():
    return {
        'relays': DEFAULT_RELAY,
        'bot_account': Keys(USE_KEY)
    }


class BotEventHandler(EventHandler):

    def __init__(self, as_user: Keys, clients: ClientPool):
        self._as_user = as_user
        self._clients = clients                
        super().__init__(event_acceptors=[DeduplicateAcceptor()])

    def _make_reply_tags(self, src_evt: Event) -> []:
        """
            minimal tagging just that we're replying to sec_evt and tag in the creater pk so they see our reply
        """
        return [
            ['p', src_evt.pub_key]
           # ['e', src_evt.id, 'reply']
        ]

    def do_event(self, the_client: Client, sub_id: str, evt: [Event]):
        # replying to ourself would be bad! also call accept_event
        # to stop us replying mutiple times if we see the same event from different relays
        if evt.pub_key == self._as_user.public_key_hex() or \
                self.accept_event(the_client, sub_id, evt) is False:
            return

        logger.debug('BotEventHandler::do_event - received event %s' % evt)
        prompt_text, response_text = self.handle_bot_command(evt)
        # logger.debug('BotEventHandler::do_event - prompt = %s' % prompt_text)
        logger.debug('BotEventHandler::do_event - response = %s' % response_text)

        # create and send
        response_event = Event(
            kind=evt.kind,
            content=response_text,
            tags=self._make_reply_tags(evt),
            pub_key=self._as_user.public_key_hex()
        )

        if response_event.kind == Event.KIND_ENCRYPT:
            response_event.content = response_event.encrypt_content(priv_key=self._as_user.private_key_hex(),
                                                                    pub_key=evt.pub_key)

        response_event.sign(self._as_user.private_key_hex())
        self._clients.publish(response_event)
        if self._store:
            # store the txt decrypted?
            if evt.kind == Event.KIND_ENCRYPT:
                evt.content = prompt_text
                response_event.content = response_text

            asyncio.create_task(self._store.put(prompt_evt=evt,
                                                reply_evt=response_event))


    def menu(self):
        return """ ***** BoltCard Bot Commander *****
/help - lists available commands
/freeze <card_name> - disables card
/enable <card_name> - (re)enables card
/get <card_name> - shows card settings
/tx_max <card_name> <sats> - sets new tx maximum
/day_max <card_name> <sats> - sets new daily max
"""


    def handle_bot_command(self, the_event):        
        prompt_text = the_event.content
        if the_event.kind == Event.KIND_ENCRYPT:
            prompt_text = the_event.decrypted_content(priv_key=self._as_user.private_key_hex(),
                                                      pub_key=the_event.pub_key)

        # do whatever to get the response
        # pk = the_event.pub_key
        # reply_n = self._replied[pk] = self._replied.get(pk, 0)+1
        # reply_name = util_funcs.str_tails(pk)        
        match prompt_text.split():
            case ["/freeze", card_name]:
                response_text = f'frozen {card_name}'
            
            case ["/get", card_name]:
                response_text = f'get {card_name}'

            case ["/enable", card_name]:
                response_text = f'enabled {card_name}' 

            case ["/tx_max", card_name, sats]:
                response_text = f'tx max {card_name} {sats}'  

            case ["/day_max", card_name, sats]:
                response_text = f'day max {card_name} {sats}'          

            case _: response_text = self.menu()
        #response_text = self.menu() #f'hey {reply_name} this is reply to you'

        return prompt_text, response_text


async def start_bot():    
    args = get_args()
    # admin_user = await get_user(bot_settings.admin)
    # admin_key = admin_user.wallets[0].adminkey
    logger.debug(f"starting nostrboltcardbot")
    # just the keys, change to profile?
    as_user = args['bot_account']

    # relays we'll watch
    relays = args['relays']
    last_since = LastEventHandler()
    sub_id = None
    # the actually clientpool obj
    my_clients = ClientPool(clients=relays.split(','))

    # do_event of this class is called on recieving events that match teh filter we reg for
    my_handler = BotEventHandler(as_user=as_user,
                                  clients=my_clients)
    # class PrintHandler(EventHandler):
    #     def __init__(self, as_user: Keys, clients: ClientPool):
    #         self._as_user = as_user
    #         self._clients = clients            
    #         super().__init__(event_acceptors=[DeduplicateAcceptor()])

    #     def do_event(self, the_client: Client, sub_id: str, evt: [Event]):
    #         if evt.pub_key == self._as_user.public_key_hex() or \
    #             self.accept_event(the_client, sub_id, evt) is False:                
    #             return
    #         print_event('ON_EVENT', evt)

    #my_handler = PrintHandler(as_user=as_user, clients=my_clients)

    # def print_event(rec_type:str, evt: Event):
    #     logger.debug('%s-%s:: %s - %s' % (evt.created_at.date(),
    #                                rec_type,
    #                                util_funcs.str_tails(evt.id),
    #                                evt.content))
    # called on first connect and any reconnects, registers our event listener
    def on_connect(the_client: Client):
        nonlocal sub_id
        sub_id = the_client.subscribe(sub_id='bot_watch',
                             handlers=[my_handler],
                             filters={
                                 'kinds': [Event.KIND_ENCRYPT],
                                 '#p': [as_user.public_key_hex()]                                                            
                             })
        if last_since.get_last_event_dt(the_client):
             filter['since'] = util_funcs.date_as_ticks(last_since.get_last_event_dt(the_client))+1

    def on_eose(the_client: Client, sub_id:str, events: [Event]):
        # so newest events come in at the bottom
        Event.sort(events, inplace=True, reverse=False)
        # for evt in events:
        #     print_event('EOSE', evt)
        last_since.set_now(the_client)
        # for evt in events:
        #     the_client.publish(evt)
        #     break
   
    # add the on_connect
    my_clients.set_on_connect(on_connect)
    my_clients.set_on_eose(on_eose)
   #my_clients.on_notice(on_notice)

    # start the clients
    logger.debug('monitoring for events from or to account %s on relays %s' % (as_user.public_key_hex(),
                                                                        relays))
    await my_clients.run()

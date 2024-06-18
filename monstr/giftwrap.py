import json
import random
from datetime import datetime
from .signing.signing import SignerInterface, BasicKeySigner
from .encrypt import Keys
from .event.event import Event
from .util import util_funcs


class GiftWrapException(Exception):
    pass


class GiftWrap:
    """
        implementation of NIP59 https://github.com/nostr-protocol/nips/blob/master/59.md
        replaces our inbox class
    """
    def __init__(self, signer: SignerInterface):
        self._signer = signer
        # jitter is upto 2 days from now
        self._jitter = 60 * 60 * 24 * 2

    def get_jittered_created_ticks(self):
        return util_funcs.date_as_ticks(datetime.now()) - random.SystemRandom().randint(0, self._jitter)

    async def _make_rumour(self, evt: Event) -> Event:
        """
            A rumor is the same thing as an unsigned event.
            Any event kind can be made a rumor by removing the signature.
            so we just return a copy evt but make sure no sig, pubkey is us
            end it's seralised with these val
        """

        event_data = evt.data()
        event_data['sig'] = None
        event_data['pubkey'] = await self._signer.get_public_key()
        event_data['kind'] = Event.KIND_RUMOUR

        ret = Event.load(event_data)
        # this forces the id, oxchat didn't see the events without this
        ret.id
        # forces id to be calculated
        return ret

    async def _make_seal(self,
                         rumour_evt: Event,
                         to_pub_k: Keys | str) -> Event:

        if rumour_evt.sig:
            raise GiftWrapException('GiftWrap::_make_seal: rumour event should not be signed!')

        if isinstance(to_pub_k, Keys):
            to_pub_k = to_pub_k.public_key_hex()

        ret = Event(kind=Event.KIND_SEAL,
                    content=await self._signer.nip44_encrypt(plain_text=json.dumps(rumour_evt.data()),
                                                             to_pub_k=to_pub_k),
                    created_at=self.get_jittered_created_ticks(),
                    pub_key=await self._signer.get_public_key(),
                    tags=[])

        await self._signer.sign_event(ret)
        return ret

    async def wrap(self, evt: Event, to_pub_k: Keys | str, pow: int = None) -> tuple[Event, Keys]:
        if isinstance(to_pub_k, Keys):
            to_pub_k = to_pub_k.public_key_hex()

        rumour_evt = await self._make_rumour(evt)
        sealed_evt = await self._make_seal(rumour_evt, to_pub_k)

        rnd_k = Keys()
        rnd_sign = BasicKeySigner(rnd_k)

        ret = Event(kind=Event.KIND_GIFT_WRAP,
                    pub_key=rnd_k.public_key_hex(),
                    created_at=self.get_jittered_created_ticks(),
                    content=await rnd_sign.nip44_encrypt(plain_text=json.dumps(sealed_evt.data()),
                                                         to_pub_k=to_pub_k),
                    tags=[
                        ['p', to_pub_k]
                    ])

        if pow is not None:
            ret.add_pow(pow)

        await rnd_sign.sign_event(ret)
        return ret, rnd_k

    async def _unwrap(self, evt: Event) -> Event:
        wrapped_str = await self._signer.nip44_decrypt(evt.content, evt.pub_key)
        return Event.load(wrapped_str)

    async def unwrap(self, evt: Event):
        to_pub_k = evt.tags.get_tag_value_pos('p')
        our_pub_k = await self._signer.get_public_key()

        if to_pub_k is None:
            raise GiftWrapException('wraped event is not addressed to anyone, no p ptags!')
        if to_pub_k != our_pub_k:
            raise GiftWrapException(f'wraped event is not addressed to us,'
                                    f' {util_funcs.str_tails(our_pub_k)} != {util_funcs.str_tails(to_pub_k)}')

        # unwrap the seal event
        seal_evt = await self._unwrap(evt)
        # unseal (unwrap again)
        rumour_evt = await self._unwrap(seal_evt)
        return rumour_evt
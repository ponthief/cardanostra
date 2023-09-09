import json
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


from .crud import (       
    get_nostrbotcard_by_uid,    
    update_nostrbot_card,
    check_card_owned_by_npub,
    get_boltcard_by_uid,
    update_boltcard,
    get_npub_cards,
    insert_card,
    get_relays,
    get_nostr_accounts
)

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
        ]

    async def do_event(self, the_client: Client, sub_id: str, evt: [Event]):
        # replying to ourself would be bad! also call accept_event
        # to stop us replying mutiple times if we see the same event from different relays
        if evt.pub_key == self._as_user.public_key_hex() or \
                self.accept_event(the_client, sub_id, evt) is False:
            return

        logger.debug('BotEventHandler::do_event - received event %s' % evt)
        prompt_text, response_text = await self.handle_bot_command(evt)
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
/help - shows this menu
/freeze <card_name> - disables card
/enable <card_name> - (re)enables card
/get <card_name> - shows card settings
/tx_max <card_name> <sats> - sets new tx maximum
/day_max <card_name> <sats> - sets new daily max
/list - displays all the cards registered to pub key
/register <uid> <card_name> - register new card
"""

    async def get_card_details(self, card_name, pub_key):                         
        the_card = await check_card_owned_by_npub(card_name, pub_key)        
        if the_card is not None:
            bcard = await get_boltcard_by_uid(the_card.uid)
            if bcard is None:
               return 'Card must be added through BoltCards extension first.'                       
            return str(bcard)
        return f'{card_name} not found. Register first via /register command.'
    

    async def change_card_settings(self, card_name, pub_key, **csettings):                         
        the_card = await check_card_owned_by_npub(card_name, pub_key)        
        if the_card is not None:
            bcard = await get_boltcard_by_uid(the_card.uid)
            if bcard is None:
               return 'Card must be added through BoltCards extension first.'
            updt_bcard = await update_boltcard(the_card.uid, **csettings)            
            return str(updt_bcard)
        return f'{card_name} not found. Register first via /register command.'
    

    async def list_cards_for_npub(self, pub_key):
        card_names = await get_npub_cards(pub_key)
        if card_names is None:
            return 'No BoltCards found. Register first via /register command.'
        return f'Registered cards: {card_names}'
    
    async def get_uid_len(self, uid):
        return await len(bytes.fromhex(uid))
    
    async def register_card(self, uid, card_name, pub_key):                
        # uid_len = await self.get_uid_len(uid)
        # if uid_len != 7:
        #     return f'{uid} is not valid card UID.'
        card = await get_nostrbotcard_by_uid(uid)
        if card is not None:
            return 'Nothing to do. Card already registered.'        
        logger.debug("valid uid") 
        await insert_card(uid.upper(), pub_key, card_name)
        card = await get_nostrbotcard_by_uid(uid)
        if card is None:
            return 'Failed to register card.'
        return "Card successfully registered."

    async def handle_bot_command(self, the_event):        
        prompt_text = the_event.content
        if the_event.kind == Event.KIND_ENCRYPT:
            prompt_text = the_event.decrypted_content(priv_key=self._as_user.private_key_hex(),
                                                      pub_key=the_event.pub_key)

        # do whatever to get the response
        pk = the_event.pub_key
        # reply_n = self._replied[pk] = self._replied.get(pk, 0)+1
        # reply_name = util_funcs.str_tails(pk) 
        # logger.debug(reply_name)       
        match prompt_text.split():
            case ["/freeze", card_name]:                
                response_text = await self.change_card_settings(card_name, pk, enable=False)
            
            case ["/get", card_name]:
                response_text = await self.get_card_details(card_name, pk)

            case ["/enable", card_name]:                
                response_text = await self.change_card_settings(card_name, pk, enable=True)

            case ["/tx_max", card_name, sats]:                
                response_text = await self.change_card_settings(card_name, pk, tx_limit=sats)  

            case ["/day_max", card_name, sats]:                
                response_text = await self.change_card_settings(card_name, pk, daily_limit=sats)   

            case ["/list"]:
                response_text = await self.list_cards_for_npub(pk)  

            case ["/register", uid, card_name]:
                response_text = await self.register_card(uid, card_name, pk)     

            case _: response_text = self.menu()
        #response_text = self.menu() #f'hey {reply_name} this is reply to you'

        return prompt_text, response_text
    


async def start_bot():    
    #args = get_args()    
    logger.debug(f"starting nostrboltcardbot")
    # just the keys, change to profile?
    #as_user = args['bot_account']               
    accounts = [account.nsec for account in await get_nostr_accounts()]    
    if len(accounts) == 0:
        raise RuntimeError("Nostr account private key must be added for Bot to start.")
    relays = ','.join([relay.url for relay in await get_relays()])
    if len(relays) == 0:
        raise RuntimeError("At least 1 Nostr Relay must be added for Bot to start.")    
    #relays = args['relays']
    last_since = LastEventHandler()
    sub_id = None    
    my_clients = ClientPool(clients=relays.split(','))
    as_user = Keys(accounts[0])
    my_handler = BotEventHandler(as_user=as_user, clients=my_clients)    
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
        last_since.set_now(the_client)        
   
    # add the on_connect
    my_clients.set_on_connect(on_connect)
    my_clients.set_on_eose(on_eose)
   #my_clients.on_notice(on_notice)

    # start the clients
    logger.debug('monitoring for events from or to account %s on relays %s' % (as_user.public_key_hex(),
                                                                        relays))
    #await my_clients.run()
    while True:
        try:
            for cli in my_clients:
                if not cli._is_connected:
                    await cli.run()
            await asyncio.sleep(20)                      
        except Exception as e:
            logger.warning(f"Cannot restart relays: '{str(e)}'.")

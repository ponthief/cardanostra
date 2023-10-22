import asyncio
from lnbits.extensions.cardanostra.monstr.client.client import Client, ClientPool
from lnbits.extensions.cardanostra.monstr.event_handlers import EventHandler, DeduplicateAcceptor
from lnbits.extensions.cardanostra.monstr.event import Event
from lnbits.extensions.cardanostra.monstr.encrypt import Keys
from loguru import logger

from .crud import (       
    get_nostrbotcard_by_uid,    
    check_card_owned_by_npub,
    get_boltcard_by_uid,
    update_boltcard,
    get_npub_cards,
    insert_card,
    get_boltcard_bal,
    get_boltcard_spent_day
)


class NostrBot(EventHandler):

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

    # This async function will raise an exception
    async def async_restart(self):
        await asyncio.sleep(1)
        raise Exception("We need to restart")


    def menu(self):
        return """ ***** CardaNostra Commands *****
/help - shows this menu
/freeze <card_name> - disables card
/enable <card_name> - (re)enables card
/get <card_name> - shows card settings
/tx_max <card_name> <sats> - sets new tx maximum
/day_max <card_name> <sats> - sets new daily max
/list - displays all the cards registered to pub key
/register <uid> <card_name> - register new card
/bal <card_name> - display card balance
/spent <card_name> - total spent today
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
        bcard = await get_boltcard_by_uid(uid)
        if bcard is None:
            return 'Card must be added through BoltCards extension first.'
        card = await get_nostrbotcard_by_uid(uid)
        if card is not None:
            return 'Nothing to do. Card already registered.'                 
        await insert_card(uid.upper(), pub_key, card_name)
        card = await get_nostrbotcard_by_uid(uid)
        if card is None:
            return 'Failed to register card.'
        return "Card successfully registered."
    
    async def get_bal_for_card(self, card_name, pub_key):                         
        the_card = await check_card_owned_by_npub(card_name, pub_key)        
        if the_card is not None:
            bcard = await get_boltcard_by_uid(the_card.uid)
            if bcard is None:
               return 'Card must be added through BoltCards extension first.'
            card_bal = await get_boltcard_bal(the_card.uid)            
            return f'Remaining balance for {card_name}: {card_bal} sats'
        return f'{card_name} not found. Register first via /register command.'
    
    async def get_day_spent_for_card(self, card_name, pub_key):                         
        the_card = await check_card_owned_by_npub(card_name, pub_key)        
        if the_card is not None:
            bcard = await get_boltcard_by_uid(the_card.uid)
            if bcard is None:
               return 'Card must be added through BoltCards extension first.'
            card_spent = await get_boltcard_spent_day(the_card.uid)            
            return f"Spent today on {card_name}: {card_spent} sats"
        return f'{card_name} not found. Register first via /register command.'
    
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

            case ["/bal", card_name]:
                response_text = await self.get_bal_for_card(card_name, pk)

            case ["/spent", card_name]:
                response_text = await self.get_day_spent_for_card(card_name, pk)           

            case _: response_text = self.menu()
        #response_text = self.menu() #f'hey {reply_name} this is reply to you'

        return prompt_text, response_text
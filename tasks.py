import asyncio
from typing import Optional
from loguru import logger
from .nostrbot import NostrBot
import httpx
from lnbits.extensions.nostrboltcardbot.monstr.util import util_funcs
from lnbits.extensions.nostrboltcardbot.monstr.client.client import Client, ClientPool
from lnbits.extensions.nostrboltcardbot.monstr.event_handlers import LastEventHandler
from lnbits.extensions.nostrboltcardbot.monstr.event import Event
from lnbits.extensions.nostrboltcardbot.monstr.encrypt import Keys
from lnbits.core.models import Payment
from lnbits.helpers import get_current_extension_name
from lnbits.tasks import register_invoice_listener

from .crud import (          
    get_relays,
    get_nostr_accounts
)

http_client: Optional[httpx.AsyncClient] = None
#DEFAULT_RELAY = 'wss://nostr-pub.wellorder.net,wss://nos.lol'
# DEFAULT_RELAY = 'ws://localhost:8888'
DEFAULT_RELAY = 'wss://nos.lol'
# bot account priv_k - to remove hardcode
USE_KEY = ''
global clients

# def get_args():
#     return {
#         'relays': DEFAULT_RELAY,
#         'bot_account': Keys(USE_KEY)
#     }
    
async def start_bot():
    global clients    
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
    clients = ClientPool(clients=relays.split(','))
    as_user = Keys(accounts[0])
    handler = NostrBot(as_user=as_user, clients=clients) 

   
    def on_connect(the_client: Client):
        nonlocal sub_id
        sub_id = the_client.subscribe(sub_id='bot_watch',
                             handlers=[handler],
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
    clients.set_on_connect(on_connect)
    clients.set_on_eose(on_eose)   

    # start the clients
    logger.debug('monitoring for events from or to account %s on relays %s' % (as_user.public_key_hex(),
                                                                        relays))
    # await clients.run()
    await check_reconnect()

# async def wait_for_paid_invoices():
#     invoice_queue = asyncio.Queue()
#     register_invoice_listener(invoice_queue, get_current_extension_name())

#     while True:
#         payment = await invoice_queue.get()
#         await on_invoice_paid(payment)


# async def on_invoice_paid(payment: Payment) -> None:

#     if not payment.extra.get("refund"):
#         return

#     if payment.extra.get("wh_status"):
#         # this webhook has already been sent
#         return

#     hit = await get_hit(str(payment.extra.get("refund")))

#     if hit:
#         await create_refund(hit_id=hit.id, refund_amount=(payment.amount / 1000))
#         await mark_webhook_sent(payment, 1)


async def check_reconnect():
    while True:        
        try:
            for cli in clients:
                if not cli._is_connected:
                    await cli.run()                                  
            await asyncio.sleep(20)
        except Exception as e:
            logger.warning(f"Cannot restart relays: '{str(e)}'.")

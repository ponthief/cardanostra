import asyncio
from typing import Optional
from loguru import logger
from .cardanostra import CardaNostra
import httpx
import datetime
from lnbits.extensions.cardanostra.monstr.util import util_funcs
from lnbits.extensions.cardanostra.monstr.client.client import Client, ClientPool
from lnbits.extensions.cardanostra.monstr.event_handlers import LastEventHandler
from lnbits.extensions.cardanostra.monstr.event import Event
from lnbits.extensions.cardanostra.monstr.encrypt import Keys
from .crud import (          
    get_relays,
    get_nostr_accounts
)
from . import scheduled_tasks
from lnbits.tasks import catch_everything_and_restart

http_client: Optional[httpx.AsyncClient] = None
global NClients
NClients = None

async def setup_bot():    
    accounts = [account.nsec for account in await get_nostr_accounts()] 
    relays = ','.join([relay.url for relay in await get_relays()])
    return accounts, relays


async def start_bot():     
    #args = get_args()  
    global NClients       
    logger.debug(f"starting cardanostra")
    accounts, relays = await setup_bot() 
    if len(accounts) == 0:
        logger.warning("Nostr Account private key must be added in UI for CardaNostra to function.")
        return       
    if len(relays) == 0:
        logger.warning("At least 1 Nostr Relay must be added for CardaNostra to function.")              
    # just the keys, change to profile?
    #as_user = args['bot_account'] 
    last_since = LastEventHandler()   
    clients = ClientPool(clients=relays.split(','))
    as_user = Keys(accounts[0])
    handler = CardaNostra(as_user=as_user, clients=clients)                 
    sub_id = None   
    NClients = clients

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
    if as_user and relays:
        logger.debug('monitoring for events from or to account %s on relays %s'
                    % (as_user.public_key_hex(), relays))
        await clients.run()         


async def restart_bot():
    global NClients
    if NClients:
        NClients.end()
    NClients = None
    logger.info("Restarting CardaNostra")
    loop = asyncio.get_event_loop()
    task1 = loop.create_task(catch_everything_and_restart(start_bot))
    task1.set_name("CardaNostra")            
    scheduled_tasks.append(task1)
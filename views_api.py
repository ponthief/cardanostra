# views_api.py is for you API endpoints that could be hit by another service

# add your dependencies here

from http import HTTPStatus
from fastapi import Depends
from starlette.exceptions import HTTPException
from lnbits.decorators import check_admin
from lnbits.helpers import urlsafe_short_hash
from . import nostrboltcardbot_ext
from loguru import logger

from .crud import (   
    add_nostr_account,
    add_relay,
    set_nostrbot_card_data,
    delete_nostrbot_card,    
    get_nostrbotcard_by_uid,    
    get_boltcard_by_uid,
    get_cards,
    get_nostr_accounts,
    get_relays,
    get_account_by_id,
    get_relay_by_id,
    delete_nostr_account,
    delete_nostr_relay,
    get_account_by_nsec,
    get_relay_by_url   
)
from .models import (   
    NostrCardData,
    NostrAccount,
    RelayData
)
from .helpers import normalize_public_key, validate_private_key
from .tasks import start_bot, stop_bot


def validate_card(data: NostrCardData):
    try:
        if len(bytes.fromhex(data.uid)) != 7:
            raise HTTPException(
                detail="Invalid bytes for card uid.", status_code=HTTPStatus.BAD_REQUEST
            )  
        if normalize_public_key(data.npub) is None:    
            raise HTTPException(
                detail="Invalid pubkey provided.", status_code=HTTPStatus.BAD_REQUEST
            )      
    except Exception:
        raise HTTPException(
            detail="Invalid byte data provided.", status_code=HTTPStatus.BAD_REQUEST
        )  
    

def validate_account(data: NostrAccount):
    try:        
        if not validate_private_key(data.nsec):    
            raise HTTPException(
                detail="Invalid private key provided.", status_code=HTTPStatus.BAD_REQUEST
            )      
    except Exception:
        raise HTTPException(
            detail="Invalid private key provided.", status_code=HTTPStatus.BAD_REQUEST
        )

# add your endpoints here
# @nostrboltcardbot_ext.put("/api/v1/restart")
# async def restart_nostr_client(wallet: WalletTypeInfo = Depends(require_admin_key)):
#     try:
#         await nostr_client.restart()
#     except Exception as ex:
#         logger.warning(ex)

# Account Control

@nostrboltcardbot_ext.get("/api/v1/accounts", status_code=HTTPStatus.OK, 
                          dependencies=[Depends(check_admin)])
async def api_accounts():   
    return [account.dict() for account in await get_nostr_accounts()] 

@nostrboltcardbot_ext.delete("/api/v1/accounts/{id}",
                             dependencies=[Depends(check_admin)])
async def delete_account(id: str): 
    checkId = await get_account_by_id(id)
    if checkId is None:
        raise HTTPException(
            detail="Nostr account does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostr_account(id)
    return "", HTTPStatus.NO_CONTENT 

@nostrboltcardbot_ext.post(
    "/api/v1/account",
    description="Add new Nostr account",
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(validate_account), Depends(check_admin)]
)
async def api_add_nostr_account(
    data: NostrAccount
):
    data.id = urlsafe_short_hash()
    account_exist = await get_account_by_nsec(data.nsec)
    if account_exist:
        raise HTTPException(
            detail="Nostr account already added.", status_code=HTTPStatus.BAD_REQUEST
        )            
    account = await add_nostr_account(data)    
    
    if not account:
        raise HTTPException(
            detail="Nostr account not added.", status_code=HTTPStatus.NOT_FOUND
        )   
    assert account, "add account should always return an account"     
    return account

# Relay Control

@nostrboltcardbot_ext.get("/api/v1/relays", status_code=HTTPStatus.OK,
                          dependencies=[Depends(check_admin)])
async def api_relays():       
    return [relay.dict() for relay in await get_relays()] 


@nostrboltcardbot_ext.post(
    "/api/v1/relay",
    description="Add new Relay",    
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(check_admin)])
async def api_add_relay(
    data: RelayData
):
    rel_exist = await get_relay_by_url(data.url)
    if rel_exist:
        raise HTTPException(
            detail="Nostr Relay already added.", status_code=HTTPStatus.BAD_REQUEST
        )
    
    data.id = urlsafe_short_hash()
    relay = await add_relay(data)    
    
    if not relay:
        raise HTTPException(
            detail="Nostr Relay not added.", status_code=HTTPStatus.NOT_FOUND
        )   
    assert relay, "add relay should always return a relay"     
    return relay

@nostrboltcardbot_ext.delete("/api/v1/relays/{id}", dependencies=[Depends(check_admin)])
async def delete_relay(id: str): 
    checkId = await get_relay_by_id(id)
    if checkId is None:
        raise HTTPException(
            detail="Relay does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostr_relay(id)
    return "", HTTPStatus.NO_CONTENT 

# Card Control

@nostrboltcardbot_ext.post("/api/v1/register", 
                           status_code=HTTPStatus.CREATED,
                           dependencies=[Depends(validate_card), Depends(check_admin)])
async def set_card(data: NostrCardData): 
    checkBUid = await get_boltcard_by_uid(data.uid)
    if checkBUid is None:
        raise HTTPException(
            detail="UID not registered in BoltCards extension. Add it there first.",
            status_code=HTTPStatus.BAD_REQUEST,
        ) 
    checkUid = await get_nostrbotcard_by_uid(data.uid)
    if checkUid:
        raise HTTPException(
            detail="UID already registered. Delete registered card and try again.",
            status_code=HTTPStatus.BAD_REQUEST,
        ) 
    card = await set_nostrbot_card_data(data)
    assert card, "create_card should always return a card"
    return card      

@nostrboltcardbot_ext.delete("/api/v1/cards/{card_uid}", dependencies=[Depends(check_admin)])
async def delete_card(card_uid: str): 
    checkUid = await get_nostrbotcard_by_uid(card_uid)
    if not checkUid:
        raise HTTPException(
            detail="Card does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostrbot_card(card_uid)
    return "", HTTPStatus.NO_CONTENT 

@nostrboltcardbot_ext.get("/api/v1/cards", status_code=HTTPStatus.OK, dependencies=[Depends(check_admin)])
async def api_cards():   
    logger.debug([card.dict() for card in await get_cards()])
    return [card.dict() for card in await get_cards()]      
# Bot 

@nostrboltcardbot_ext.post("/api/v1/restart")
async def api_restart_bot():    
    await stop_bot()
    # await start_bot()

# @nostrboltcardbot_ext.post(
#     "api/v1/relay",
#     description="Add new relay",
#     status_code=HTTPStatus.OK,
#     dependencies=[Depends(validate_account)]
# )
# async def api_add_relay(
#     data: NostrRelayData
# ):
#     bot_settings = await add_relay(data)    
    # if wallet_type.wallet.id == settings.super_user:
    #         client = await start_bot(bot_settings)
    # else:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Only the super user can add new relay",
    #     )    
    # return BotInfo.from_client(bot_settings, client)


# async def api_add_relay(
#     data: NostrAccountData
# ):
#     bot_settings = await add_relay(data)    
#     # if wallet_type.wallet.id == settings.super_user:
#     #         client = await start_bot(bot_settings)
#     # else:
#     #     raise HTTPException(
#     #         status_code=400,
#     #         detail="Only the super user can add new relay",
#     #     )    
#     # return BotInfo.from_client(bot_settings, client)
# @nostrboltcardbot_ext.delete(
#     "/api/v1/delete",
#     status_code=HTTPStatus.OK,
# )
# async def api_delete_bot(bot_settings: BotSettings = Depends(require_bot_settings)):
#     if not bot_settings.standalone:
#         await stop_bot()
#     await delete_nostrboltbot_settings(bot_settings.admin)


# @nostrboltcardbot_ext.patch(
#     "/api/v1/update",
#     status_code=HTTPStatus.OK,
# )
# async def api_update_bot(
#     data: UpdateBotSettings, bot_settings: BotSettings = Depends(require_bot_settings)
# ):
#     bot_settings = await update_nostrboltbot_settings(data, bot_settings.admin)
#     if not bot_settings.standalone:
#         await start_bot(bot_settings)


# @nostrboltcardbot_ext.get("/api/v1/start", status_code=HTTPStatus.OK, 
#                           response_model=BotInfo)
# async def api_bot_start(bot_settings: BotSettings = Depends(require_bot_settings)):
#     if bot_settings.standalone:
#         raise HTTPException(status_code=400, detail="Standalone bot cannot be started")
#     client = await start_bot(bot_settings)
#     return BotInfo.from_client(bot_settings, client)


# @nostrboltcardbot_ext.get("/api/v1/stop", status_code=HTTPStatus.OK, response_model=BotInfo)
# async def api_bot_stop(bot_settings: BotSettings = Depends(require_bot_settings)):
#     if bot_settings.standalone:
#         raise HTTPException(status_code=400, detail="Standalone bot cannot be stopped")
#     client = await stop_bot()
#     return BotInfo.from_client(bot_settings, client)


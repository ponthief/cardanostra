# views_api.py is for you API endpoints that could be hit by another service

# add your dependencies here

from http import HTTPStatus
from fastapi import Depends, Query
from starlette.exceptions import HTTPException
from lnbits.decorators import WalletTypeInfo, require_admin_key
from lnbits.helpers import urlsafe_short_hash
from . import nostrboltcardbot_ext
from loguru import logger

from .crud import (   
    add_nostr_account,
    add_relay,
    set_nostrbot_card_data,
    delete_nostrbot_card,    
    get_nostrbotcard_by_uid,    
    update_nostrbot_card,
    get_boltcard_by_uid,
    get_cards,
    get_nostr_accounts    
)
from .models import (
    # BotInfo,
    # BotSettings,
    # CreateBotSettings,    
    # UpdateBotSettings,
    NostrCardData,
    NostrAccount,
    RelayData
)
from .helpers import normalize_public_key, validate_private_key
# try:
#     from .tasks import  start_bot

#     can_run_bot = True
# except ImportError as e:    

#     async def start_bot():
#         return None    

#     raise    


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


# async def require_bot_settings(
#     wallet_info: WalletTypeInfo = Depends(require_admin_key),
# ):
#     settings = await get_nostrboltbot_settings(wallet_info.wallet.user)
#     if not settings:
#         raise HTTPException(status_code=400, detail="No bot created")
#     if not settings.standalone and not can_run_bot:
#         raise HTTPException(
#             status_code=400, detail="Can not run Nostr BoltCard Bot bots on this instance"
#         )
#     return settings


# @nostrboltcardbot_ext.delete("/api/v1/settings", status_code=HTTPStatus.OK)
# async def api_extension_delete(usr: str = Query(...)):
#     settings = await get_nostrboltbot_settings(usr)
#     if settings:
#         await stop_bot()
#         await delete_nostrboltbot_settings(settings.admin)


# # Card Control

@nostrboltcardbot_ext.post("/api/v1/register", 
                           status_code=HTTPStatus.CREATED,
                           dependencies=[Depends(validate_card)])
async def set_card(data: NostrCardData): 
    checkBUid = await get_boltcard_by_uid(data.uid)
    if checkBUid is None:
        raise HTTPException(
            detail="UID not registered in BoltCards extension. Please add card first.",
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

# @nostrboltcardbot_ext.post("/api/v1/cardupdate", status_code=HTTPStatus.OK)
# async def update_card(data: NostrCardData):    
#     return update_nostrbot_card(data)

@nostrboltcardbot_ext.delete("/api/v1/cards/{card_uid}")
async def delete_nostrbot_card(card_uid: str, wallet: WalletTypeInfo = Depends(require_admin_key)): 
    checkUid = await get_nostrbotcard_by_uid(card_uid)
    if not checkUid:
        raise HTTPException(
            detail="Card does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostrbot_card(card_uid)
    return "", HTTPStatus.NO_CONTENT 

@nostrboltcardbot_ext.get("/api/v1/cards")
async def api_cards():   
    logger.debug([card.dict() for card in await get_cards()])
    return [card.dict() for card in await get_cards()]      
# # Bot Accounts


@nostrboltcardbot_ext.get("/api/v1/accounts")
async def api_accounts():   
    logger.debug([account.dict() for account in await get_nostr_accounts()])
    return [account.dict() for account in await get_nostr_accounts()] 


@nostrboltcardbot_ext.post(
    "/api/v1/account",
    description="Add new nostr account",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(validate_account)]
)
async def api_add_nostr_account(
    data: NostrAccount
):
    data.id = urlsafe_short_hash()
    account = await add_nostr_account(data)    
    
    if not account:
        raise HTTPException(
            detail="Nostr account not added.", status_code=HTTPStatus.NOT_FOUND
        )        
    return "", HTTPStatus.NO_CONTENT

@nostrboltcardbot_ext.post(
    "/api/v1/relay",
    description="Add new Relay",
    status_code=HTTPStatus.OK
)
async def api_add_relay(
    data: RelayData
):
    data.id = urlsafe_short_hash()
    relay = await add_relay(data)    
    
    if not relay:
        raise HTTPException(
            detail="Nostr Relay not added.", status_code=HTTPStatus.NOT_FOUND
        )        
    return "", HTTPStatus.NO_CONTENT

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


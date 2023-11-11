# views_api.py is for you API endpoints that could be hit by another service

# add your dependencies here

from http import HTTPStatus
from fastapi import Depends
from starlette.exceptions import HTTPException
from lnbits.decorators import WalletTypeInfo, require_admin_key
from lnbits.helpers import urlsafe_short_hash
from . import cardanostra_ext
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
from .tasks import restart_bot


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

# Account Control

@cardanostra_ext.get("/api/v1/accounts", status_code=HTTPStatus.OK)
async def api_accounts(wallet: WalletTypeInfo = Depends(require_admin_key)):   
    return [account.dict() for account in await get_nostr_accounts()] 

@cardanostra_ext.delete("/api/v1/accounts/{id}")
async def delete_account(id: str, wallet: WalletTypeInfo = Depends(require_admin_key)): 
    checkId = await get_account_by_id(id)
    if checkId is None:
        raise HTTPException(
            detail="Nostr account does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostr_account(id)
    return "", HTTPStatus.NO_CONTENT 

@cardanostra_ext.post(
    "/api/v1/account",
    description="Add new Nostr account",
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(validate_account)]
)
async def api_add_nostr_account(wallet: WalletTypeInfo = Depends(require_admin_key),
    data: NostrAccount = None
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

@cardanostra_ext.get("/api/v1/relays", status_code=HTTPStatus.OK)
async def api_relays(wallet: WalletTypeInfo = Depends(require_admin_key)):       
    return [relay.dict() for relay in await get_relays()] 


@cardanostra_ext.post(
    "/api/v1/relay",
    description="Add new Relay",    
    status_code=HTTPStatus.CREATED)
async def api_add_relay( wallet: WalletTypeInfo = Depends(require_admin_key),
    data: RelayData = None
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

@cardanostra_ext.delete("/api/v1/relays/{id}")
async def delete_relay(id: str, wallet: WalletTypeInfo = Depends(require_admin_key)): 
    checkId = await get_relay_by_id(id)
    if checkId is None:
        raise HTTPException(
            detail="Relay does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostr_relay(id)
    return "", HTTPStatus.NO_CONTENT 

# Card Control

@cardanostra_ext.post("/api/v1/register", 
                           status_code=HTTPStatus.CREATED,
                           dependencies=[Depends(validate_card)])
async def set_card(wallet: WalletTypeInfo = Depends(require_admin_key), data: NostrCardData = None): 
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

@cardanostra_ext.delete("/api/v1/cards/{card_uid}")
async def delete_card(card_uid: str, wallet: WalletTypeInfo = Depends(require_admin_key)): 
    checkUid = await get_nostrbotcard_by_uid(card_uid)
    if not checkUid:
        raise HTTPException(
            detail="Card does not exist.", status_code=HTTPStatus.NOT_FOUND
        )    
    await delete_nostrbot_card(card_uid)
    return "", HTTPStatus.NO_CONTENT 

@cardanostra_ext.get("/api/v1/cards", status_code=HTTPStatus.OK)
async def api_cards(wallet: WalletTypeInfo = Depends(require_admin_key)):    
    return [card.dict() for card in await get_cards()]  
    
# Bot 

@cardanostra_ext.put("/api/v1/restart")
async def api_restart_bot(wallet: WalletTypeInfo = Depends(require_admin_key)):    
    await restart_bot()
    return {"success": True}  

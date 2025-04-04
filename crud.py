from typing import List, Optional
from lnbits.db import Database
from .models import Card, NostrCardData, NostrBotCard, BCard, NostrAccount
from .helpers import normalize_public_key
from loguru import logger
from .models import RelayData,  NostrAccountData

db = Database("ext_cardanostra")

# Relays
async def get_relays() -> List[RelayData]:
    rows = await db.fetchall("SELECT * FROM cardanostra.relays")
    return [RelayData(**row) for row in rows]


async def get_relay_by_id(id: str) -> Optional[RelayData]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.relays WHERE id = :id", {"id": id},
        RelayData
    )    

async def get_relay_by_url(url: str) -> Optional[RelayData]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.relays WHERE url = :url", {"url": url},
        RelayData
    )


async def add_relay(relay: RelayData) -> None:
    await db.execute(
        f"""
        INSERT INTO cardanostra.relays (
            id,
            url            
        )
        VALUES (:id, :url)
        """,
        {
        "id"   :relay.id,
        "url" :relay.url
        },        
    )
    relay = await get_relay_by_id(relay.id)
    assert relay, "Nostr Relay couldn't be retrieved"
    return relay


async def delete_nostr_relay(id: str) -> None:
    await db.execute("DELETE FROM cardanostra.relays WHERE id = :id", {"id": id})

# Accounts

async def get_nostr_accounts() -> List[NostrAccount]:
    rows = await db.fetchall("SELECT * FROM cardanostra.accounts")
    return [NostrAccount(**row) for row in rows]


async def add_nostr_account(account: NostrAccount) -> NostrAccountData:   
    await db.execute(
        f"""
        INSERT INTO cardanostra.accounts (
            id,
            nsec            
        )
        VALUES (:id, :nsec)
        """,
        {
        "id"   :account.id,
        "nsec" :account.nsec
        },
    )
    account = await get_account_by_id(account.id)
    assert account, "Newly created Nostr account couldn't be retrieved"
    return account


async def get_account_by_id(id: str) -> Optional[NostrAccount]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.accounts WHERE id = :id", {"id": id},
        NostrAccount
    )   

async def get_account_by_nsec(nsec: str) -> Optional[NostrAccount]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.accounts WHERE nsec = :nsec", {"nsec": nsec},
        NostrAccount
    )    

async def delete_nostr_account(id: str) -> None:
    await db.execute("DELETE FROM cardanostra.accounts WHERE id = :id", {"id": id})


# Cards
async def insert_card(uid, npub, card_name):
    await db.execute(
        """
        INSERT INTO cardanostra.cards (            
            uid,            
            npub,
            card_name            
        )
            VALUES (:uid, :npub, :card_name)
        """,
        {           
          "uid"  :uid, 
          "npub" :npub,                       
          "card_name" :card_name,            
        },
    )


async def set_nostrbot_card_data(data: NostrCardData) -> NostrBotCard: 
    npub_hex = normalize_public_key(data.npub) 
    await insert_card(data.uid.upper(), npub_hex, data.card_name)    
    card = await get_nostrbotcard_by_uid(data.uid)
    assert card, "Newly created card couldn't be retrieved"
    return card


async def get_nostrbotcard_by_uid(uid: str) -> Optional[NostrBotCard]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.cards WHERE uid = :uid", {"uid": uid},
        NostrBotCard
    )

async def check_card_owned_by_npub(card_name: str, npub: str) -> Optional[NostrBotCard]:
    return await db.fetchone(
        "SELECT * FROM cardanostra.cards WHERE card_name = :card_name and npub = :npub", {"card_name": card_name, "npub": npub},
        NostrBotCard
    )

async def get_npub_cards(npub: str) -> Optional[list]:    
    rows = await db.fetchall(
        "SELECT card_name FROM cardanostra.cards WHERE npub = :npub", {"npub": npub}
    )
    if not rows:        
        return None            
    cards = [' '.join(card.values()) for card in rows]         
    return ', '.join(cards)

async def get_cards() -> List[NostrBotCard]:    
    rows = await db.fetchall("SELECT * FROM cardanostra.cards")
    return [NostrBotCard(**row) for row in rows]

async def delete_nostrbot_card(uid: str) -> None:
    # Delete cards
    await db.execute("DELETE FROM cardanostra.cards WHERE uid = :uid", {"uid": uid.upper()})

async def get_boltcard_by_uid(uid: str) -> Optional[BCard]:
    return await db.fetchone(
        "SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = :uid", {"uid": uid.upper()},
        BCard
    )

async def update_boltcard(uid: str, **kwargs) -> Optional[BCard]:
    if not kwargs:
        return "No card/incorrect setting specified"   
    col = [k for k in kwargs.keys()]
    val = [v for v in kwargs.values()]      
    if col[0] == 'enable':
        await db.execute(f"UPDATE boltcards.cards SET enable = :val WHERE uid = :uid", {"val" : val[0], "uid": uid.upper()})
    elif col[0] == 'tx_limit':
        if val[0].isnumeric():            
            await db.execute(f"UPDATE boltcards.cards SET tx_limit = :val WHERE uid = :uid", {"val" : val[0], "uid": uid.upper()})
    elif col[0] == 'daily_limit':
        if val[0].isnumeric():
            await db.execute(f"UPDATE boltcards.cards SET daily_limit = :val WHERE uid = :uid", {"val" : val[0], "uid": uid.upper()})
    return await db.fetchone(
        "SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = :uid", {"uid": uid.upper()},
        BCard
    )


async def get_boltcard_bal(uid: str) -> Optional[int]:    
    row = await db.fetchone(
        "SELECT wallet FROM boltcards.cards WHERE uid = :uid", {"uid": uid.upper()}        
    )       
    if row:        
        row = await db.fetchone(
        "SELECT balance FROM public.balances WHERE wallet_id = :wallet_id", {"wallet_id": row.get('wallet')}        
    )
        if row:
            return int(row.get('balance')/1000)
    return 0

async def get_boltcard_spent_day(uid: str) -> Optional[int]:    
    row = await db.fetchone(
        "SELECT wallet FROM boltcards.cards WHERE uid = :uid", {"uid": uid.upper()}        
    )
    if row:
        row = await db.fetchone(
                    "SELECT sum(amount) FROM public.apipayments WHERE wallet_id = :wallet_id AND "
                    "time BETWEEN date_trunc('day', NOW()) - INTERVAL '1 day' "
                    "AND LOCALTIMESTAMP", {"wallet_id": row.get('wallet')}        
    )
        if row:
            if row.get("sum") is None:
                return 0
            return abs(int(row.get("sum")/1000))        
    return 0
from typing import List, Optional
from . import db
from .models import Card, NostrCardData, NostrBotCard, BCard, NostrAccount

from .helpers import normalize_public_key
from loguru import logger

from .models import RelayData,  NostrAccountData

# Relays
async def get_relays() -> List[RelayData]:
    rows = await db.fetchall("SELECT * FROM cardanostra.relays")
    return [RelayData(**row) for row in rows]


async def get_relay_by_id(id: str) -> Optional[RelayData]:
    row = await db.fetchone(
        "SELECT * FROM cardanostra.relays WHERE id = ?", (id)
    )
    if not row:
        return None

    relay = dict(**row)

    return RelayData.parse_obj(relay)


async def get_relay_by_url(url: str) -> Optional[RelayData]:
    row = await db.fetchone(
        "SELECT * FROM cardanostra.relays WHERE url = ?", (url)
    )
    if not row:
        return None

    relay = dict(**row)

    return RelayData.parse_obj(relay)


async def add_relay(relay: RelayData) -> None:
    await db.execute(
        f"""
        INSERT INTO cardanostra.relays (
            id,
            url            
        )
        VALUES (?, ?)
        """,
        (relay.id, relay.url),
    )
    relay = await get_relay_by_id(relay.id)
    assert relay, "Nostr Relay couldn't be retrieved"
    return relay


async def delete_nostr_relay(id: str) -> None:
    await db.execute("DELETE FROM cardanostra.relays WHERE id = ?", (id))

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
        VALUES (?, ?)
        """,
        (account.id, account.nsec),
    )
    account = await get_account_by_id(account.id)
    assert account, "Newly created Nostr account couldn't be retrieved"
    return account


async def get_account_by_id(id: str) -> Optional[NostrAccount]:
    row = await db.fetchone(
        "SELECT * FROM cardanostra.accounts WHERE id = ?", (id)
    )
    if not row:
        return None

    account = dict(**row)

    return NostrAccount.parse_obj(account)


async def get_account_by_nsec(nsec: str) -> Optional[NostrAccount]:
    row = await db.fetchone(
        "SELECT * FROM cardanostra.accounts WHERE nsec = ?", (nsec)
    )
    if not row:
        return None

    account = dict(**row)

    return NostrAccount.parse_obj(account)

async def delete_nostr_account(id: str) -> None:
    await db.execute("DELETE FROM cardanostra.accounts WHERE id = ?", (id))


# Cards
async def insert_card(uid, npub, card_name):
    await db.execute(
        """
        INSERT INTO cardanostra.cards (            
            uid,            
            npub,
            card_name            
        )
            VALUES (?, ?, ?)
        """,
        (            
            uid, 
            npub,                       
            card_name,            
        ),
    )


async def set_nostrbot_card_data(data: NostrCardData) -> NostrBotCard: 
    npub_hex = normalize_public_key(data.npub) 
    await insert_card(data.uid.upper(), npub_hex, data.card_name)    
    card = await get_nostrbotcard_by_uid(data.uid)
    assert card, "Newly created card couldn't be retrieved"
    return card


async def get_nostrbotcard_by_uid(uid: str) -> Optional[NostrBotCard]:
    row = await db.fetchone(
        "SELECT * FROM cardanostra.cards WHERE uid = ?", (uid.upper(),)
    )
    if not row:
        return None

    card = dict(**row)

    return NostrBotCard.parse_obj(card)


async def check_card_owned_by_npub(card_name: str, npub: str) -> Optional[NostrBotCard]:    
    row = await db.fetchone(
        "SELECT * FROM cardanostra.cards WHERE card_name = ? AND npub = ?", (card_name, npub)
    )
    if not row:        
        return None    
    card = dict(**row)    
    return NostrBotCard.parse_obj(card)


async def get_npub_cards(npub: str) -> Optional[list]:    
    rows = await db.fetchall(
        "SELECT card_name FROM cardanostra.cards WHERE npub = ?", (npub)
    )
    if not rows:        
        return None         
    cards = [' '.join(card) for card in rows]         
    return ', '.join(cards)

async def get_cards() -> List[NostrBotCard]:    
    rows = await db.fetchall("SELECT * FROM cardanostra.cards")
    return [NostrBotCard(**row) for row in rows]


async def update_nostrbot_card(uid: str, **kwargs) -> Optional[NostrBotCard]:
    # npub_hex = normalize_public_key(data.npub)   
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE cardanostra.cards SET {q} WHERE uid = ?",
        (*kwargs.values(), uid.upper()),
    )
    row = await db.fetchone("SELECT * FROM cardanostra.cards WHERE uid = ?", (kwargs["uid"].upper(),))
    return NostrBotCard(**row) if row else None

async def delete_nostrbot_card(uid: str) -> None:
    # Delete cards
    await db.execute("DELETE FROM cardanostra.cards WHERE uid = ?", (uid.upper()))


async def get_boltcard_by_uid(uid: str) -> Optional[Card]:    
    row = await db.fetchone(
        "SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = ?", (uid.upper())
    )    
    if not row:
        return None

    card = dict(**row)    
    return BCard.parse_obj(card)


async def update_boltcard(uid: str, **kwargs) -> Optional[BCard]:        
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])    
    await db.execute(
        f"UPDATE boltcards.cards SET {q} WHERE uid = ?",
        (*kwargs.values(), uid.upper()),
    )    
    row = await db.fetchone("SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = ?", (uid.upper()))
    return BCard(**row) if row else None


async def get_boltcard_bal(uid: str) -> Optional[int]:          
    row = await db.fetchone("SELECT wallet FROM boltcards.cards WHERE uid = ?", (uid.upper()))
    if row:
        row = await db.fetchone("SELECT balance FROM public.balances WHERE wallet = ?", (row[0]))
        if row[0]:
            return int(row[0]/1000)
    return 0

async def get_boltcard_spent_day(uid: str) -> Optional[int]:
    row = await db.fetchone("SELECT wallet FROM boltcards.cards WHERE uid = ?", (uid.upper()))
    if row:
        row = await db.fetchone("SELECT sum(amount) FROM public.apipayments WHERE wallet = ? AND "
                                "time >= date_trunc('day', NOW()) - INTERVAL '1 day' "
                                "AND time <  date_trunc('day', NOW())", (row[0]))
        logger.debug(row)
        if row[0]:
            return abs(int(row[0]/1000))        
    return 0
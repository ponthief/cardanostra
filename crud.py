from typing import  List, Optional
from . import db
from .models import Card, NostrCardData, NostrBotCard, BCard
from .models import BotSettings, CreateBotSettings, UpdateBotSettings
from .helpers import normalize_public_key
from loguru import logger

async def get_nostrboltbot_settings(admin_id: str) -> Optional[BotSettings]:
    row = await db.fetchone(
        "SELECT * FROM nostrboltcardbot.cardbot WHERE admin = ?", (admin_id,)
    )
    return BotSettings(**row) if row else None

async def get_all_nostrboltbot_settings() -> list[BotSettings]:
    rows = await db.fetchall("SELECT * FROM nostrboltcardbot.cardbot")
    return [BotSettings(**row) for row in rows]


async def create_nostrboltbot_settings(data: CreateBotSettings, admin_id: str):
    await db.execute(
        f"""
        INSERT INTO nostrboltcardbot.cardbot (admin,privkey,relay, standalone) 
        VALUES (?, ?, ?, ?)        
        """,
        (admin_id, data.privkey, data.relay, data.standalone),
    )
    return await get_nostrboltbot_settings(admin_id)

async def update_nostrboltbot_settings(data: UpdateBotSettings, admin_id: str):
    updates = []
    values = []
    for key, val in data.dict(exclude_unset=True).items():
        updates.append(f"{key} = ?")
        values.append(val)
    values.append(admin_id)
    await db.execute(
        f"""
        UPDATE nostrboltcardbot.cardbot 
        SET {", ".join(updates)}
        WHERE admin = ?
        """,
        values,
    )
    return await get_nostrboltbot_settings(admin_id)


async def delete_nostrboltbot_settings(admin_id: str):
    result = await db.execute(
        "DELETE FROM nostrboltcardbot.cardbot WHERE admin = ?", (admin_id,)
    )
    assert result.rowcount == 1, "Could not create settings"
# crud.py is for communication with your extensions database
# Card DB
async def set_nostrbot_card_data(data: NostrCardData) -> NostrBotCard: 
    npub_hex = normalize_public_key(data.npub)       
    await db.execute(
        """
        INSERT INTO nostrboltcardbot.cards (            
            uid,            
            npub,
            card_name            
        )
            VALUES (?, ?, ?)
        """,
        (            
            data.uid.upper(), 
            npub_hex,                       
            data.card_name,            
        ),
    )
    card = await get_nostrbotcard_by_uid(data.uid.upper())
    assert card, "Newly created card couldn't be retrieved"
    return card

async def get_nostrbotcard_by_uid(uid: str) -> Optional[NostrBotCard]:
    row = await db.fetchone(
        "SELECT * FROM nostrboltcardbot.cards WHERE uid = ?", (uid.upper(),)
    )
    if not row:
        return None

    card = dict(**row)

    return NostrBotCard.parse_obj(card)


async def check_card_owned_by_npub(card_name: str, npub: str) -> Optional[NostrBotCard]:    
    row = await db.fetchone(
        "SELECT * FROM nostrboltcardbot.cards WHERE card_name = ? AND npub = ?", (card_name, npub)
    )
    if not row:        
        return None    
    card = dict(**row)
    logger.debug(NostrBotCard.parse_obj(card))
    return NostrBotCard.parse_obj(card)


async def get_cards() -> List[NostrBotCard]:    
    rows = await db.fetchall("SELECT * FROM nostrboltcardbot.cards")
    return [NostrBotCard(**row) for row in rows]


async def update_nostrbot_card(uid: str, **kwargs) -> Optional[NostrBotCard]:    
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE nostrboltcardbot.cards SET {q} WHERE uid = ?",
        (*kwargs.values(), uid.upper()),
    )
    row = await db.fetchone("SELECT * FROM nostrboltcardbot.cards WHERE uid = ?", (kwargs["uid"].upper(),))
    return NostrBotCard(**row) if row else None

async def delete_nostrbot_card(uid: str) -> None:
    # Delete cards
    await db.execute("DELETE FROM nostrboltcardbot.cards WHERE uid = ?", (uid.upper(),))


async def get_boltcard_by_uid(uid: str) -> Optional[Card]:
    logger.debug(uid.upper())
    row = await db.fetchone(
        "SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = ?", (uid.upper(),)
    )    
    if not row:
        return None

    card = dict(**row)
    logger.debug(BCard.parse_obj(card))
    return BCard.parse_obj(card)

async def update_boltcard(uid: str, **kwargs) -> Optional[BCard]:  
    logger.debug('try update')  
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    logger.debug(q)
    await db.execute(
        f"UPDATE boltcards.cards SET {q} WHERE uid = ?",
        (*kwargs.values(), uid.upper()),
    )    
    row = await db.fetchone("SELECT tx_limit, daily_limit, enable FROM boltcards.cards WHERE uid = ?", (uid.upper(),))
    return BCard(**row) if row else None
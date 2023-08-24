from typing import  Optional
from . import db
from .models import Card, NostrCardData, NostrBotCard
from .models import BotSettings, CreateBotSettings, UpdateBotSettings


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
    boltcard = await get_boltcard_by_uid(data.uid.upper())
    assert boltcard, f"BoltCard with uid: {data.uid} not registered."
    await db.execute(
        """
        INSERT INTO nostrboltcardbot.cards (            
            uid,            
            npub,
            card_name            
        )
            VALUES (?, ?, ?,)
        """,
        (            
            data.uid.upper(), 
            data.npub,                       
            data.cardname,            
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
    await db.execute("DELETE FROM nostrboltcardbot.cards WHERE uid = ?", (uid,))

async def get_boltcard_by_uid(uid: str) -> Optional[Card]:
    row = await db.fetchone(
        "SELECT * FROM nostrboltcardbot.cards WHERE uid = ?", (uid.upper(),)
    )
    if not row:
        return None

    card = dict(**row)

    return Card.parse_obj(card)    
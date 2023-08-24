from lnbits.db import SQLITE, Database


async def m004_add_cards_bot(db):

    await db.execute(
        """
        CREATE TABLE nostrboltcardbot.cards (            
            uid TEXT PRIMARY KEY, 
            npub TEXT NOT NULL,           
            card_name TEXT NOT NULL                    
        );
    """
    )   
    await db.execute(
        """
        CREATE TABLE nostrboltcardbot.cardbot (            
            admin TEXT PRIMARY KEY,
            privkey TEXT NOT NULL UNIQUE,
            relay TEXT NOT NULL,
            standalone BOOLEAN NOT NULL DEFAULT TRUE
        );
    """
    )

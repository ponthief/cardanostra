from lnbits.db import SQLITE, Database


async def m004_add_cards(db):

    await db.execute(
        """
        CREATE TABLE nostrboltcardbot.cards (            
            uid TEXT PRIMARY KEY, 
            npub TEXT NOT NULL,           
            card_name TEXT NOT NULL                    
        );
    """
    ) 


async def m005_add_relays_accounts(db):

      
    await db.execute(
        """
         CREATE TABLE nostrboltcardbot.relays (
            id TEXT NOT NULL PRIMARY KEY,
            url TEXT NOT NULL,
            active BOOLEAN DEFAULT true
        );
    """
    )

    await db.execute(
        """
        CREATE TABLE nostrboltcardbot.accounts (            
            id TEXT NOT NULL PRIMARY KEY,
            nsec TEXT NOT NULL                 
        );
    """
    )

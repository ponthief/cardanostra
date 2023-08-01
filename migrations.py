from lnbits.db import SQLITE, Database


async def m001_initial(db):
    """
    Initial settings table.
    """
    await db.execute(
        """
        CREATE TABLE nostrboltbot.bot (
        admin TEXT PRIMARY KEY,
                CONSTRAINT admin_account_id 
                FOREIGN KEY(admin)
                REFERENCES accounts(id)
                ON DELETE cascade,
            privkey TEXT NOT NULL UNIQUE,
            relay TEXT NOT NULL,
            standalone BOOLEAN NOT NULL DEFAULT TRUE           
        );
    """
    ) 
async def m002_add_cards(db):
    await db.execute(
        """
        CREATE TABLE nostrboltbot.cards (            
            uid TEXT PRIMARY UNIQUE, 
            npub TEXT NOT NULL           
            card_name TEXT NOT NULL,                     
        );
    """
    )   

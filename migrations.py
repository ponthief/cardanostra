
async def m001_initial(db):

    await db.execute(
        """
        CREATE TABLE cardanostra.cards (            
            uid TEXT PRIMARY KEY, 
            npub TEXT NOT NULL,           
            card_name TEXT NOT NULL                    
        );
    """
    ) 
      
    await db.execute(
        """
         CREATE TABLE cardanostra.relays (
            id TEXT NOT NULL PRIMARY KEY,
            url TEXT NOT NULL,
            active BOOLEAN DEFAULT true
        );
    """
    )

    await db.execute(
        """
        CREATE TABLE cardanostra.accounts (            
            id TEXT NOT NULL PRIMARY KEY,
            nsec TEXT NOT NULL                 
        );
    """
    )

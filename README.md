# CardaNostra - Nostr BoltCard Managament - <small>[LNbits](https://github.com/lnbits/lnbits) extension</small>
<small>For more about BoltCard LNBits extensions check [this tutorial](https://youtu.be/_sW7miqaXJc)</small>


This extension allows you to control your [Bolt Card](https://github.com/boltcard) via Nostr account. 
It requires that the [BoltCards Extension](https://github.com/lnbits/boltcards) for Lnbits is installed and activated.
Once BoltCard(s) are added via BoltCards Extension, Administrator account can:
- Add a Nostr Account which will act as a Bot handling requests from the users with BoltCards
- Link BoltCard to user's Nostr account so that the card/account are authorised to communicate with the Bot
- Add Nostr Relays so that NIP-04 messages between Bot and BoltCard user's Nostr account can be sent


## Add Main Nostr Account

- Add Nostr Account in the extension.
    - Click on "Add Nostr Account" button and enter NSec key of the Nostr account.
    - Make note of the NPub as this is the account that users with BoltCards will have to Follow via their clients (Amethyst etc.)

## Add Relays

- Add Nostr Relays in the extension.
    - Click on "Add Nostr Relay" button and enter one of the well known public relays or your own relay.
    - Enter relay endpoint in the format: "wss://relay" i.e. wss://nos.lol
  
## Register Existing BoltCard

- Assign BoltCard to user controlled Nostr Account
    - Click on "Register Existing BoltCard" - NOTE: Card must exist in the BoltCards Extension database.
    - Enter Card's UID - it is unique identifier for the card which is available when card is created through BoltCards extension.
    - Enter Card Name - this is the name that the user would like his card to be known as i.e. MyLnBitsBoltCard
    - Enter NPub - this is Public Key for the Nostr Account that also "owns" the card and wishes to control it via Bot
    
Once all 3 items are added into LNbits users with cards who are following LNbits Nostr account will be able to manage their cards by sending direct encrypted messages:
<p float="left">
<img src= "https://github.com/ponthief/cardanostra/blob/main/static/cardanostra_menu.jpg" width="300" height="575">
<img src= "https://github.com/ponthief/cardanostra/blob/main/static/cardanostra_commands.jpg" width="300" height="575">
</p>
from __future__ import annotations
# from pynostr.relay_manager import RelayManager
# from pynostr.filters import FiltersList, Filters
# from pynostr.event import EventKind
from fastapi import Depends, Request, WebSocket
from lnbits.extensions.relay.client_manager import NostrClientConnection, NostrClientManager
from lnbits.extensions.relay.relay import NostrRelay
import uuid
from typing import TYPE_CHECKING
from httpx import AsyncClient

from .api import LnbitsAPI
from .settings import nostrbot_settings


DEV_GUILD = None

client_manager = NostrClientManager()
class LnbitsClient():
    def __init__(
        self,
        *,
        admin_key: str,
        http: AsyncClient,
        lnbits_url: str,
        data_folder: str,
        bot_priv_key: str,
        nostr_relay: str,
        **options,
    ):
        super().__init__(**options)
        self.admin_key = admin_key        
        self.lnbits_url = lnbits_url
        self.data_folder = data_folder
        self.bot_priv_key = bot_priv_key
        self.nostr_relay = nostr_relay
        self.api = LnbitsAPI(admin_key=admin_key, http=http, lnbits_url=lnbits_url)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        if DEV_GUILD:
            self.tree.copy_global_to(guild=DEV_GUILD)
        await self.tree.sync(guild=DEV_GUILD)

    


class LnbitsInteraction():
    if TYPE_CHECKING:

        @property
        def client(self) -> LnbitsClient:
            """:class:`Client`: The client that is handling this interaction.

            Note that :class:`AutoShardedClient`, :class:`~.commands.Bot`, and
            :class:`~.commands.AutoShardedBot` are all subclasses of client.
            """
            return self._client  # type: ignore

        @property
        def response(self):
            """:class:`Client`: The client that is handling this interaction.

            Note that :class:`AutoShardedClient`, :class:`~.commands.Bot`, and
            :class:`~.commands.AutoShardedBot` are all subclasses of client.
            """
            return self.response  # type: ignore



def create_client(admin_key: str, http: AsyncClient, lnbits_url: str, data_folder: str, priv_key: str,nostr_relay: str):
    client = LnbitsClient(        
        admin_key=admin_key,
        http=http,
        lnbits_url=lnbits_url,
        data_folder=data_folder,
        bot_priv_key=priv_key,
        nostr_relay=nostr_relay
    )

    @client.event
    async def on_ready():
        print(f"Connecting to Nostr relay(s))")
        print("------")
        client_accepted = await client_manager.add_client(client)
        if not client_accepted:
            return

        try:
            await client.start()
        except Exception as e:
            logger.warning(e)
            client_manager.remove_client(client)
        # relay_manager = RelayManager(timeout=2)
        # relay_manager.add_relay("wss://nostr-pub.wellorder.net")
        # relay_manager.add_relay("wss://relay.damus.io")
        # relay_manager.add_relay(client.nostr_relay)
        # filters = FiltersList([Filters(authors=[client.bot_priv_key.public_key.hex()], limit=100)])
        # subscription_id = uuid.uuid1().hex
        # relay_manager.add_subscription_on_all_relays(subscription_id, filters)        
        # relay_manager.run_sync()
        
           
    # async def donate(interaction: LnbitsInteraction, amount: int, description: str):
    #     wallet = await client.api.get_user_wallet(interaction.user)

    #     await client.api.request(
    #         "POST",
    #         "/extensions",
    #         extension="usermanager",
    #         params={"userid": wallet.user, "extension": "withdraw", "active": True},
    #     )

    #     resp = await client.api.request(
    #         method="post",
    #         path="/links",
    #         extension="withdraw",
    #         key=wallet.adminkey,
    #         json={
    #             "title": description,
    #             "min_withdrawable": amount,
    #             "max_withdrawable": amount,
    #             "uses": 1,
    #             "wait_time": 1,
    #             "is_unique": True,
    #         },
    #     )

    #     await interaction.response.send_message(
    #         embed=discord.Embed(
    #             title="Donation",
    #             description=f"{interaction.user.mention} is donating **{get_amount_str(amount)}**",
    #             color=discord.Color.yellow(),
    #         )
    #         .add_field(name="Description", value=description)
    #         .add_field(name="LNURL", value=resp["lnurl"], inline=False),
    #         view=discord.ui.View().add_item(ClaimButton(lnurl=resp["lnurl"])),
    #     )

        

    return client
from __future__ import annotations
from loguru import logger
import logging
import websocket
import rel
from fastapi import Depends, Request, WebSocket
from lnbits.extensions.nostrrelay.relay.client_manager import NostrClientConnection, NostrClientManager
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
        # nostr_relay: str,
        **options,
    ):
        super().__init__(**options)
        self.admin_key = admin_key        
        self.lnbits_url = lnbits_url
        self.data_folder = data_folder
        self.bot_priv_key = bot_priv_key
        # self.nostr_relay = nostr_relay
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



def create_client(admin_key: str, http: AsyncClient, lnbits_url: str, data_folder: str, priv_key: str):
    client = LnbitsClient(        
        admin_key=admin_key,
        http=http,
        lnbits_url=lnbits_url,
        data_folder=data_folder,
        bot_priv_key=priv_key,
        # nostr_relay=nostr_relay
    )

    @client.event
    async def on_ready():
        logging.debug('BotEventHandler::started')
        print("------")
        ws = websocket.WebSocketApp("wss://nostr-pub.wellorder.net")
        ws.run_forever(dispatcher=rel, reconnect=5)
        rel.dispatch()
        client = NostrClientConnection(relay_id="nostrbitbest", websocket=ws)
        client_accepted = await client_manager.add_client(client)
        if not client_accepted:
            return

        try:
            await client.start()
        except Exception as e:
            logger.warning(e)
            client_manager.remove_client(client)
        # wss://bolt.bitbest.net/nostrrelay/nostrbitbest        

        

    return client
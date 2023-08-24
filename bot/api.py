from __future__ import annotations

from typing import Optional
from httpx import AsyncClient, HTTPStatusError

from .models import Card
from .settings import nostrbot_settings



class LnbitsAPI:
    def __init__(
        self, *, admin_key: str, http: AsyncClient, lnbits_url: str, **options
    ):
        super().__init__(**options)
        self.admin_key = admin_key
        self.lnbits_http = http
        self.lnbits_url = lnbits_url        
    

    # async def get_user_cards(self, user_id: str ) -> Optional[Card]:      
    #     wallets = await self.request(
    #         "GET",
    #         f'/wallets/{user_id}',
    #         self.admin_key,
    #         extension="usermanager",
    #     )
    #     if wallets:
    #         cards = await self.request(
    #         "GET",
    #         '/cards',
    #         self.admin_key,
    #         extension="boltcards",
    #         params={"wallet": str(discord_user.id)},
    #     )
    #     # wallet = Wallet(**wallets[0])
                
    #     return cards
        

    async def request(
        self, method: str, path: str, key: str = None, extension: str = None, **kwargs
    ) -> dict:
        if key:
            self.lnbits_http.headers["X-API-KEY"] = key

        response = await self.lnbits_http.request(
            method,
            url=self.lnbits_url
            + (extension + "/" if extension else "")
            + "api/v1"
            + path,
            **kwargs,
        )

        response.raise_for_status()

        return response.json()

   
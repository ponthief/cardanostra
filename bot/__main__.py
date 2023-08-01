import asyncio
from bot.client import create_client
from httpx import AsyncClient

from .settings import StandaloneSettings

settings = StandaloneSettings()


async def run():
    async with AsyncClient() as http:
        if not settings.data_folder.is_dir():
            settings.data_folder.mkdir()
        client = create_client(
            settings.lnbits_admin_key,
            http,
            settings.lnbits_url,
            str(settings.data_folder),
            settings.nostr_bot_privkey
        )               

        async with client:
            await client.start()


def start_bot():
    asyncio.run(run())


if __name__ == "__main__":
    start_bot()
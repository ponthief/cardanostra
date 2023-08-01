from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Extra, HttpUrl


class NostrBotSettings(BaseSettings):
    nostr_dev_guild: Optional[int] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = Extra.ignore


class StandaloneSettings(NostrBotSettings):
    lnbits_url: HttpUrl
    lnbits_admin_key: str
    nostr_bot_privkey: Optional[str] = None
    nostr_relay: Optional[str] = None    
    data_folder: Optional[Path] = "/data"


nostrbot_settings = NostrBotSettings()
from __future__ import annotations
from sqlite3 import Row
from pydantic import BaseModel
from fastapi import Query
from sqlite3 import Row
from typing import Optional  


class BotSettings(BaseModel):
    admin: str  
    privkey: str
    relay: str  
    standalone: bool


class CreateBotSettings(BaseModel): 
    privkey: str
    relay: str   
    standalone: bool


class UpdateBotSettings(BaseModel):
    privkey: str
    relay: str    
    standalone: Optional[bool]


class BotInfo(BotSettings):
    online: Optional[bool]

    @classmethod
    def from_client(cls, settings: BotSettings):
        return cls(**settings.dict())
    
class Card(BaseModel):
    id: str
    wallet: str
    card_name: str
    uid: str
    external_id: str
    counter: int
    tx_limit: int
    daily_limit: int
    enable: bool
    k0: str
    k1: str
    k2: str
    prev_k0: str
    prev_k1: str
    prev_k2: str
    otp: str
    time: int

    @classmethod
    def from_row(cls, row: Row) -> "Card":
        return cls(**dict(row))
    
class NostrCardData(BaseModel):    
    uid: str = Query(...)
    npub: str = Query(...)  
    cardname: str = Query(...)

class NostrBotCard(BaseModel):    
    uid: str
    npub: str
    cardname: str        

    @classmethod
    def from_row(cls, row: Row) -> "NostrBotCard":
        return cls(**dict(row))     
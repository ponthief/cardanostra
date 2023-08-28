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
    

class BCard(BaseModel):    
    tx_limit: int
    daily_limit: int
    enable: bool    

    def __str__(self):
        return f'Max Tx Limit: {self.tx_limit} - Max Day Limit: {self.daily_limit}, Enabled: {self.enable}'
    
    
    @classmethod
    def from_row(cls, row: Row) -> "BCard":
        return cls(**dict(row))   


class NostrCardData(BaseModel):    
    uid: str = Query(...)
    npub: str = Query(...)  
    card_name: str = Query(...)


class NostrBotCard(BaseModel):    
    uid: str
    npub: str
    card_name: str        

    @classmethod
    def from_row(cls, row: Row) -> "NostrBotCard":
        return cls(**dict(row))     
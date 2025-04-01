from pydantic import BaseModel
from fastapi import Query, Request
from typing import List, Optional 
from lnbits.helpers import urlsafe_short_hash

class RelayStatus(BaseModel):
    num_sent_events: Optional[int] = 0
    num_received_events: Optional[int] = 0
    error_counter: Optional[int] = 0
    error_list: Optional[List] = []
    notice_list: Optional[List] = []

class Relay(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    connected: Optional[bool] = None
    connected_string: Optional[str] = None
    status: Optional[RelayStatus] = None
    active: Optional[bool] = None
    ping: Optional[int] = None

    def _init__(self):
        if not self.id:
            self.id = urlsafe_short_hash()


class RelayList(BaseModel):
    __root__: List[Relay]


class RelayData(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None

    def _init__(self):
        if not self.id:
            self.id = urlsafe_short_hash()


class NostrAccount(BaseModel):
    id: Optional[str] = None
    nsec: Optional[str] = None    

    def _init__(self):
        if not self.id:
            self.id = urlsafe_short_hash()


class NostrAccountData(BaseModel):    
    #id: str = Query(...)
    nsec: str = Query(...)  


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

    

class BCard(BaseModel):    
    tx_limit: int
    daily_limit: int
    enable: bool    

    def __str__(self):
        return f'Max Tx Limit: {self.tx_limit} - Max Day Limit: {self.daily_limit}, Enabled: {self.enable}'
 


class NostrCardData(BaseModel):    
    uid: str = Query(...)
    npub: str = Query(...)  
    card_name: str = Query(...)


class NostrBotCard(BaseModel):    
    uid: str
    npub: str
    card_name: str
      
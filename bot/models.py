from pydantic import BaseModel
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
   
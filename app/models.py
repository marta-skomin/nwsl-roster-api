from pydantic import BaseModel
from typing import Optional

class Player(BaseModel):
    name: str
    number: Optional[int] = None
    age: Optional[int] = None
    country: str
    position: str
    team: str
    note: Optional[str] = None

class PlayerUpdate(BaseModel):
    number: Optional[int] = None
    age: Optional[int] = None
    country: Optional[str] = None
    note: Optional[str] = None

class SquadStats(BaseModel):
    team: str
    total_players: int
    average_age: float
    countries: list[str]
    oldest_player: str
    youngest_player: str
    positions: dict[str, int]

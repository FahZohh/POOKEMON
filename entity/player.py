from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Player:
    id: int
    username: str
    email: str
    wins: Optional[int]
    losses: Optional[int]

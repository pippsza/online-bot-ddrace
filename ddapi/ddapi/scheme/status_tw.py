# Status.tw
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class ChartEnum(StrEnum):
    day = "day"
    week = "week"
    month = "month"


class DataTw(BaseModel):
    name: str
    createdAt: datetime


class VersionTw(BaseModel):
    version: str
    createdAt: datetime


class CountryTw(BaseModel):
    identifier: str
    code: int
    iconUrl: str


class ClientTw(BaseModel):
    name: str
    country: CountryTw
    score: int
    isPlayer: bool
    isAfk: bool
    team: int
    createdAt: datetime
    clan: DataTw | None


class ServerTw(BaseModel):
    ip: str
    port: int
    name: str
    numClients: int
    numPlayers: int
    maxClients: int
    maxPlayers: int
    hasPassword: bool
    supports6: bool
    supports7: bool
    createdAt: datetime
    relevanceScore: int
    clientScoreKind: str | None
    logoUrl: str
    map: DataTw
    website: Optional[str] = None
    discordInvite: Optional[str] = None
    description: Optional[str] = None
    gameType: DataTw
    version: VersionTw
    clients: list[ClientTw]


class ServerTwOne(BaseModel):
    ip: str
    port: int
    online: ServerTw


class Chart(BaseModel):
    avgPlayers: float
    maxPlayers: int
    minPlayers: int
    timestamp: datetime


class Charts(BaseModel):
    charts: list[Chart]


class MasterTw(BaseModel):
    servers: list[ServerTw]

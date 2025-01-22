# ddnet
from typing import Optional

from pydantic import BaseModel, Field


class DPoints(BaseModel):
    total: int
    points: Optional[int] = Field(default=None)
    rank: Optional[int] = Field(default=None)


class MaxFinishes(BaseModel):
    rank: int
    player: str
    num: int
    time: float
    min_timestamp: int
    max_timestamp: int


class DDRanks(BaseModel):
    rank: int
    player: str
    time: float
    timestamp: int
    country: str


class DDTeamRanks(BaseModel):
    rank: int
    players: list[str]
    time: float
    timestamp: int
    country: str


class DMap(BaseModel):
    name: str
    website: str
    thumbnail: str
    web_preview: str
    type: str
    points: int
    difficulty: int
    mapper: str
    release: Optional[int] = None
    median_time: float
    first_finish: int
    last_finish: int
    finishes: int
    finishers: int
    biggest_team: int
    width: int
    height: int
    tiles: list[str]
    team_ranks: list[DDTeamRanks]
    ranks: list[DDRanks]
    max_finishes: list[MaxFinishes]


class DRank(BaseModel):
    points: Optional[int] = None
    rank: Optional[int] = None


class FirstFinish(BaseModel):
    timestamp: float
    map: str
    time: float


class LastFinish(BaseModel):
    timestamp: float
    map: str
    time: float
    country: str
    type: Optional[str] = None


class FavoritePartner(BaseModel):
    name: str
    finishes: int


class DData(BaseModel):
    points: Optional[DPoints] = Field(default=None)
    team_rank: Optional[DRank] = Field(default=None)
    rank: Optional[DRank] = Field(default=None)
    maps: Optional[dict] = Field(default=None)


class DDType(BaseModel):
    Novice: Optional[DData] = None
    Moderate: Optional[DData] = None
    Brutal: Optional[DData] = None
    Insane: Optional[DData] = None
    Dummy: Optional[DData] = None
    DDmaX_Easy: Optional[DData] = Field(default=None, validation_alias='DDmaX.Easy')
    DDmaX_Next: Optional[DData] = Field(default=None, validation_alias='DDmaX.Next')
    DDmaX_Nut: Optional[DData] = Field(default=None, validation_alias='DDmaX.Nut')
    DDmaX_Pro: Optional[DData] = Field(default=None, validation_alias='DDmaX.Pro')
    Oldschool: Optional[DData] = Field(default=None)
    Race: Optional[DData] = None
    Solo: Optional[DData] = None
    total: Optional[DData] = None


class Activity(BaseModel):
    date: str
    hours_played: int


class FavoriteServer(BaseModel):
    server: str


class DDPlayer(BaseModel):
    player: str
    points: DPoints
    team_rank: Optional[DRank] = None
    rank: Optional[DRank] = None
    points_last_year: Optional[DRank] = None
    points_last_month: Optional[DRank] = None
    points_last_week: Optional[DRank] = None
    favorite_server: FavoriteServer
    first_finish: FirstFinish
    last_finishes: list[LastFinish]
    favorite_partners: Optional[list[FavoritePartner]] = None
    types: DDType
    activity: list[Activity]
    hours_played_past_365_days: int

from datetime import datetime
from sqlmodel import Relationship, SQLModel, Field, String, TypeDecorator
from pydantic import EmailStr, HttpUrl


TEAM_SIZE_BY_ROLE = {"ALL": 25, "P": 3, "D": 8, "C": 8, "A": 6}
ADMIN_USER_ID = 0

class HttpUrlType(TypeDecorator):
    impl = String(2083)
    cache_ok = True

    def process_bind_param(self, value, dialect) -> str:
        return str(value)

    def process_result_value(self, value, dialect) -> HttpUrl | None:
        return HttpUrl(url=value) if value is not None else None

    def process_literal_param(self, value, dialect) -> str:
        return str(value)


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    auth0_id: str = Field(default=None, unique=True)
    email: EmailStr = Field(nullable=False, unique=True)
    budget: int = Field(nullable=False, default=500)
    team: "Team" = Relationship(back_populates="owner")
    offers: "Offer" = Relationship(back_populates="user")


class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(nullable=False, unique=True)
    full_name: str = Field(nullable=False, unique=True)
    birth_date: str = Field(nullable=False, unique=True)
    role: str = Field(nullable=False)
    img: HttpUrl = Field(nullable=False, sa_type=HttpUrlType)
    purchase_cost: int | None = Field(default=None)
    team_id: int | None = Field(default=None, foreign_key="team.id")
    real_team: str = Field(nullable=False)
    team: "Team" = Relationship(back_populates="players")
    offers: "Offer" = Relationship(back_populates="player")


class Team(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    name: str | None = Field(default=None, unique=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(back_populates="team")
    players: list[Player] = Relationship(back_populates="team")


class Offer(SQLModel, table=True):
    id: int = Field(default=None,primary_key=True, index=True)
    amount: int = Field()
    player_id: int = Field(default=None, foreign_key="player.id")
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default=datetime.now())
    user: User = Relationship(back_populates="offers")
    player: Player | None = Relationship(back_populates="offers")


class UserFrontEnd(SQLModel):
    id: int
    email: str
    team: Team

    def __init__(self, id: int, email: str, team: Team):
        self.id = id
        self.email = email
        self.team = team

# dependencies.py
from fastapi import Depends
from sqlmodel import Session
from database import get_session

# Import your classes
from repositories.offer_repository import OfferRepository
from repositories.player_repository import PlayerRepository
from repositories.team_repository import TeamRepository
from repositories.user_repository import UserRepository
from services import BiddingService

# --- Level 1: Get the Session ---
# (You already have get_session, so we use it here)

# --- Level 2: Get the Repositories ---
# These functions automatically get the session injected by FastAPI

def get_user_repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)

def get_offer_repo(session: Session = Depends(get_session)) -> OfferRepository:
    return OfferRepository(session)

def get_player_repo(session: Session = Depends(get_session)) -> PlayerRepository:
    return PlayerRepository(session)

def get_team_repo(session: Session = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)

# --- Level 3: Get the Service ---
# This function automatically gets the Repositories injected

def get_bidding_service(
    user_repo: UserRepository = Depends(get_user_repo),
    offer_repo: OfferRepository = Depends(get_offer_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
) -> BiddingService:
    return BiddingService(user_repo, offer_repo, player_repo, team_repo)
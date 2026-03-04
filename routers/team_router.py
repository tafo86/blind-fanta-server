from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from services import BiddingService
from dependencies import get_bidding_service
from models import Player, Team

router = APIRouter(
    prefix="/team",
    tags=["team"],
    responses={404: {"description": "Not found"}},
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def team(
    team: Team,
    service: BiddingService = Depends(get_bidding_service),
):  
    return service.add_team(team)


@router.get("/{team_id}/players", response_model=List[Player])
async def get_team_players(
    team_id: int,
    service: BiddingService = Depends(get_bidding_service)
):
    """
    Get the list of players for a specific team.
    Example: GET /team/5/players
    """
    players = service.get_team_players(team_id)
    return players

@router.get("/user/{user_id}", response_model=Team)
async def get_team_by_user(
    user_id: int,
    service: BiddingService = Depends(get_bidding_service)
):
    """
    Get the list of players for a specific team.
    Example: GET /team/5/players
    """
    team = service.get_team_by_user(user_id)
    if team is None:
        return JSONResponse(content={"message": "You don't have a team yet!"})
    else:
        return team
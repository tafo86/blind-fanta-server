from fastapi import APIRouter, Depends

from dependencies import get_bidding_service
from routers.auth import verify_auth0_token
from services import BiddingService

router = APIRouter(
    prefix="/player",
    tags=["player"],
    # This automatically adds 404 description to Swagger UI for all routes
    responses={404: {"description": "Not found"}}, 
)

@router.get("/players", dependencies=[Depends(verify_auth0_token)])
async def get_players(service: BiddingService = Depends(get_bidding_service)):
    """
    Get list of all players.
    """
    # No try/except needed here. 
    # If the DB fails, FastAPI/Starlette automatically returns a 500 Server Error,
    # which is correct. Returning 401 (Unauthorized) for a DB error was incorrect.
    return service.get_all_players()

@router.get("/player/{player_id}", dependencies=[Depends(verify_auth0_token)]) # Changed path to include ID in URL (RESTful standard)
async def get_player(
    player_id: int, 
    service: BiddingService = Depends(get_bidding_service)
):
    """
    Get a specific player by ID.
    """
    # The service will raise HTTPException(404) if not found,
    # so we don't need manual checks here.
    return service.get_player(player_id)
    
    

from functools import lru_cache
from fastapi import APIRouter, Depends, status
import config
from models import User
from services import BiddingService
from dependencies import get_bidding_service


router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

@lru_cache
def get_settings():
    return config.Settings()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def user_register(
    user: User,
    # settings: Annotated[config.Settings, Depends(get_settings)],
    # x_auth0_secret: Annotated[str | None, Header()] = None,
    service: BiddingService = Depends(get_bidding_service),
):
    """
    Registers a new user. 
    Returns 409 Conflict if email exists.
    """
   
    #1. Security check: Only allow Auth0 to call this
    # if x_auth0_secret != settings.CLIENT_SECRET:
    #    raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return service.register_user(user)

@router.get("/{auth_id}") # standardized URL to /user/1
async def get_user(
    auth_id: str, 
    service: BiddingService = Depends(get_bidding_service)
):
    # Fixed: The original code was missing 'return'
    return service.get_user_by_auth_id(auth_id)

@router.delete("/{user_id}") # standardized URL to /user/1
async def delete_user(
    user_id: int, 
    service: BiddingService = Depends(get_bidding_service)
):
    return service.delete_user(user_id)
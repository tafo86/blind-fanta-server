import json
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from models import ADMIN_USER_ID, Offer
from services import BiddingService
from routers import admin_router
# Import the dependency injector we created in the previous step
from dependencies import get_bidding_service 
# Import the Pydantic model defined above 

class AuctionTimeoutRequest(BaseModel):
    user_id: int
    player_id: int

router = APIRouter(
    prefix="/offer",
    tags=["offer"],
    responses={404: {"description": "Not found"}},
)

@router.get("/best/{player_id}")
async def get_best(
    player_id: int, 
    service: BiddingService = Depends(get_bidding_service)
):
    # The service handles the repo logic
    return service.offer_repo.get_best_offers_for_player(player_id)

@router.post("/save")
async def save_offer(
    offer: Offer, 
    service: BiddingService = Depends(get_bidding_service)
):
    # Logic and Validation are now inside the Service
    # If validation fails, the Service raises HTTPException, which FastAPI handles automatically
    return service.place_bid(offer)

@router.post("/timeout")
async def auction_timeout(
    payload: AuctionTimeoutRequest, 
    service: BiddingService = Depends(get_bidding_service)
):
    """
    Handles the end of an auction.
    Payload: {"user_id": 123, "player_id": 456}
    """
    #await admin_router.manager.broadcast(json.dumps({"bestOffer": offer.model_dump(mode='json')}))
    # 1. Resolve the auction (DB updates happen inside here)
    auction_result = service.resolve_auction(payload.user_id, payload.player_id)
    await admin_router.manager.send_personal_message(json.dumps({"auctionClosed":  auction_result["auctionClosed"]}), ADMIN_USER_ID)
    return service.resolve_auction(payload.user_id, payload.player_id)

@router.post("/second_round/save")
async def save_second_round_offer(offer: Offer, 
    service: BiddingService = Depends(get_bidding_service)
):
    # Logic and Validation are now inside the Service
    # If validation fails, the Service raises HTTPException, which FastAPI handles automatically
    offer_saved = service.place_bid(offer)
    if offer_saved:
        await admin_router.manager.broadcast(json.dumps({"bestOffer": offer.model_dump(mode='json')}))
    return offer_saved
    
     
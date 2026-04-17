# A simple list to track active connections (for demonstration)
import json
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request

from collections import namedtuple

from pydantic import BaseModel
from starlette import status

from dependencies import get_bidding_service
from routers.auth import verify_admin_role, verify_ws_token
from services import BiddingService

Connection = namedtuple("Connection", ["user_id", "port"])



class StartingOffer(BaseModel):
    amount: int


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        # Store connections using the user_id as the key
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

#TODO mettere a posto connessione ws con token

    async def connect(self, user_id: int, websocket: WebSocket):
        """Accepts the connection and adds it to the active pool."""
        try:
        # 1. Manually verify the token here using your PyJWKClient logic
        # (You will need to slightly adapt your verify function to accept a raw string)
        
        # 2. If it passes, accept the connection!
            await websocket.accept()
    
            if websocket.client is not None:
                port = websocket.client.port
                if user_id in self.active_connections:
                    self.active_connections[user_id][port] = websocket
                else:
                    self.active_connections[user_id] = {port: websocket}
                print(
                    f"Client {user_id} connected on port {port}. Total active: {self.get_active_connection_count()}"
                )
        except Exception:
        # If the token is invalid, close the door before they even get in
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    def disconnect(self, connection: Connection):
        """Removes the connection from the active pool."""
        if connection.user_id in self.active_connections:
            if connection.port in self.active_connections[connection.user_id]:
                del self.active_connections[connection.user_id][connection.port]
            print(
                f"Client {connection.user_id} disconnected on port {connection.port}. Total active: {self.get_active_connection_count()}"
            )

    async def send_personal_message(self, message: str, user_id: int):
        """Sends a message to a specific user."""
        if user_id in self.active_connections:
            for port, connection in self.active_connections[user_id].items():
                # We use send_json here as a best practice, but maintaining send_text for compatibility
                await connection.send_text(message)

    async def broadcast(self, message: str):
        """Sends a message to all active users."""
        # Create a list of connections to remove in case of sending failure
        disconnected_socket = []
        for user_id in self.active_connections.keys():
            for port, connection in self.active_connections[user_id].items():
                try:
                    await connection.send_text(message)
                except Exception:
                    # If sending fails, mark the connection for removal
                    disconnected_socket.append(Connection(user_id, port))

        # Clean up any failed connections
        for connection in disconnected_socket:
            self.disconnect(connection)

    def get_active_connection_count(self):
        return sum(
            len(user_connections)
            for user_connections in self.active_connections.values()
        )


# Initialize the manager globally
manager = ConnectionManager()


# --- 3. WebSocket Endpoint Refactored ---
@router.websocket("/ws/{user_id}", dependencies=[Depends(verify_ws_token)])
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    service: BiddingService = Depends(get_bidding_service),
):  # 1. Connect and add to the manager
    connection = Connection(user_id, websocket.client.port) if websocket.client is not None else None
    await manager.connect(user_id, websocket)
    try:
        # 2. Main loop for receiving messages
        while True:
            # We wrap this in a try/except to catch client disconnects
            msg = await websocket.receive_text()
            msg = json.loads(msg)
            if msg["data"] == "UPDATE_BEST_OFFER":
                best_offer = service.get_best_offers(msg["player_id"])
                await manager.broadcast(json.dumps({"offer": best_offer}))
    except WebSocketDisconnect:
        # 5. Handle cleanup when the client closes the connection
        if connection is not None:
            manager.disconnect(connection)
    except Exception as e:
        # 6. Handle other potential errors gracefully
        if connection is not None:
            print(
                f"An unexpected error occurred with client {connection.user_id} on {connection.port}: {e}"
            )
            # Ensure we always clean up if any other error occurs
            manager.disconnect(connection)
        else:
            print(f"An unexpected error occurred: {e}")


@router.post("/notify", dependencies=[Depends(verify_admin_role)])
async def brodcast(
    request: Request, service: BiddingService = Depends(get_bidding_service)
):
    # 1. Read the raw body content as bytes
    raw_body = await request.body()

    # 2. Decode the bytes to a string (assuming UTF-8 encoding)
    player_id = int(raw_body.decode("utf-8"))

    player = service.get_player(player_id)

    if player.purchase_cost is None:

        await manager.broadcast(player.model_dump_json())
        return {"eligible": True, "message": f"Successfully notified: {player.name}"}

    else:
        return {"eligible": False, "message": f"Player already bought: {player.name}"}


@router.post("/second-round")
async def second_round(
    request: Request, service: BiddingService = Depends(get_bidding_service)
):
    # 1. Read the raw body content as bytes
    raw_body = await request.body()

    # 2. Decode the bytes to a string (assuming UTF-8 encoding)
    player_id = int(raw_body.decode("utf-8"))

    player = service.get_player(player_id)

    best_offers = service.get_best_offers(player_id)

    if best_offers and len(best_offers) > 1 and best_offers[0].amount is not None:
        starting_offer = StartingOffer(amount=best_offers[0].amount)
        for offer in best_offers:
            await manager.send_personal_message(json.dumps({"startingOffer": starting_offer.model_dump(mode='json')}), offer.user.id)
            # 3. Use the string value for your logic
        return {
            "eligible": True,
            "message": f"Successfully notified second round for: {player.name}",
        }

    else:
        return {
            "eligible": False,
            "message": f"Player not eligible for second round: {player.name}",
        }
        

@router.post("/notify_second_round", status_code=200)
async def notify_second_round(
    request: Request, service: BiddingService = Depends(get_bidding_service)
):
    # 1. Read the raw body content as bytes
    raw_body = await request.body()

    # 2. Decode the bytes to a string (assuming UTF-8 encoding)
    player_id = int(raw_body.decode("utf-8"))

    best_offers = service.get_best_offers(player_id)

    if best_offers and len(best_offers) > 1:
        for offer in best_offers:
            await manager.send_personal_message(json.dumps({"info": "second_round_started"}), offer.user.id)
    
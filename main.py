from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.user_router import router as user_router
from routers.offer_router import router as offer_router
from routers.team_router import router as team_router
from routers.admin_router import router as admin_router
from routers.player_router import router as player_router


from collections import namedtuple
Connection = namedtuple('Connection', ['user_id','web_socket'])

app = FastAPI()

origins = ["http://localhost:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_router)
app.include_router(offer_router)
app.include_router(team_router)
app.include_router(admin_router)
app.include_router(player_router)

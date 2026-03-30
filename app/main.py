from fastapi import FastAPI
from app.api import bans

app = FastAPI()

app.include_router(bans.router)


from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import bans


Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(bans.router)


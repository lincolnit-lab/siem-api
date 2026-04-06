from fastapi import FastAPI
from app.db.database import engine, Base
from contextlib import asynccontextmanager
from app.api import bans




@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="SIEM API", lifespan=lifespan)

app.include_router(bans.router, prefix="/api")



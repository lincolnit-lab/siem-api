from fastapi import APIRouter, Depends
from app.services.fail2ban import get_bans, unban_ip
from app.db.database import SessionLocal
from app.db.models import Ban
from sqlalchemy.orm import Session


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/bans")
def bans():
    return get_bans()

@router.post("/unban/{ip}")
def unban(ip: str):
    return unban_ip(ip)


@router.get("/bans/active")
def get_active_bans(db: Session = Depends(get_db)):
    return db.query(Ban).filter(Ban.status == "banned").all()



@router.get("/bans/unbanned")
def get_unbanned(db: Session = Depends(get_db)):
    return db.query(Ban).filter(Ban.status == "unbanned").all()


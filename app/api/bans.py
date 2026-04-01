from fastapi import APIRouter
from app.services.fail2ban import get_bans, unban_ip
from app.db.database import SessionLocal
from app.db.models import Ban
router = APIRouter()


@router.get("/bans")
def bans():
    return get_bans()

@router.post("/unban/{ip}")
def unban(ip: str):
    return unban_ip(ip)


@router.get("/bans/active")
def get_active_bans():
    db = SessionLocal()
    try:
        return db.query(Ban). filter(Ban.status == "banned").all()
    finally:
        db.close()


@router.get("/bans/unbanned")
def get_unbanned():
    db = SessionLocal()
    try:
        return db.query(Ban).filter(Ban.status == "unbanned").all()
    finally:
        db.close

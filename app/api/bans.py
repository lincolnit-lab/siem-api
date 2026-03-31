from fastapi import APIRouter
from app.services.fail2ban import get_bans, unban_ip

router = APIRouter()


@router.get("/bans")
def bans():
    return get_bans()

@router.post("/unban/{ip}")
def unban(ip: str):
    return unban_ip(ip)
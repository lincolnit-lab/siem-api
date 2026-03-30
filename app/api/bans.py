from fastapi import APIRouter
from app.services.fail2ban import get_bans

router = APIRouter()


@router.get("/bans")
def bans():
    return get_bans()
from fastapi import APIRouter, Depends, HTTPException
from app.services.fail2ban import unban_ip
from app.db.database import AsyncSessionLocal
from app.db.models import Ban
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# ИСПРАВЛЕНО: Добавили импорт функции проверки текущего пользователя (админа)
from app.api.auth import get_current_user 

router = APIRouter(prefix="/bans")

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()

@router.get("/")
async def list_all_bans(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Возвращает абсолютно все логи банов из базы данных."""
    result = await db.execute(select(Ban))
    return result.scalars().all()

@router.post("/unban/{ip}")
async def unban(ip: str):
    """Эндпоинт разбана (открыт для локального вызова телеграм-ботом)"""
    result = await unban_ip(ip)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/active")
async def get_active_bans(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Возвращает только активные баны."""
    result = await db.execute(select(Ban).filter(Ban.status == "banned"))
    return result.scalars().all()

@router.get("/unbanned")
async def get_unbanned(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Возвращает историю разбаненных IP."""
    result = await db.execute(select(Ban).filter(Ban.status == "unbanned"))
    return result.scalars().all()
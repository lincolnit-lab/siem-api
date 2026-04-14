from fastapi import APIRouter, Depends, HTTPException
from app.services.fail2ban import get_bans, unban_ip
from app.db.database import AsyncSessionLocal
from app.db.models import Ban
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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
async def list_all_bans():
    return await get_bans()

@router.post("/unban/{ip}")
async def unban(ip: str):
    result = await unban_ip(ip)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/active")
async def get_active_bans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ban).filter(Ban.status == "banned"))
    return result.scalars().all()



@router.get("/unbanned")
async def get_unbanned(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ban).filter(Ban.status == "unbanned"))
    return result.scalars().all()


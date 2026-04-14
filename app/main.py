from fastapi import FastAPI, Depends
from app.db.database import engine, Base
from contextlib import asynccontextmanager
from app.api import bans, auth
import uvicorn
from app.services.fail2ban import get_bans
import asyncio
from bot.telegram_bot import start_telegram_bot
from app.api.auth import get_current_user



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Запуск Telegram-бота
    
    
    asyncio.create_task(start_telegram_bot())

    async def check_fail2ban():
        while True:
            await get_bans()
            await asyncio.sleep(10)

    asyncio.create_task(check_fail2ban())

    yield


# Создание приложения FastAPI
app = FastAPI(title="SIEM API", lifespan=lifespan)

# Подключение роутеров

app.include_router(auth.router, prefix="/api")



app.include_router(bans.router, prefix="/api", dependencies=[Depends(get_current_user)])

@app.get("/ping")
async def ping():
    return{"status": "ok"}


# Запуск через uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, host="0.0.0.0", reload=True)

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
import uvicorn

from app.db.database import engine, Base
from app.api import bans, auth
from app.api.auth import get_current_user
from app.services.fail2ban import watch_log_file  # Новый асинхронный воркер
from bot.telegram_bot import start_telegram_bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Автоматическое создание таблиц в PostgreSQL при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Параллельный асинхронный запуск Telegram-бота
    asyncio.create_task(start_telegram_bot())

    # Запуск непрерывного потокового мониторинга логов хоста
    asyncio.create_task(watch_log_file())

    yield

# Инициализация приложения FastAPI
app = FastAPI(title="SIEM API", lifespan=lifespan)

# Подключение роутеров
app.include_router(auth.router, prefix="/api")

# Роутер банов полностью защищен авторизацией админа
app.include_router(bans.router, prefix="/api")

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# Локальный запуск (если запускается скриптом, а не через docker-compose)
if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
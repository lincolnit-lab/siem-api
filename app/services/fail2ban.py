import re
import ipaddress
import subprocess
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db.models import Ban
from dotenv import load_dotenv
import os
from bot.telegram_bot import notify  # асинхронная функция для Telegram

LOG_FILE = os.getenv("LOG_FILE_FAIL2BAN")

async def get_bans():
    """
    Считывает новые баны из fail2ban.log и сохраняет их в базу.
    Для каждого нового бана отправляет уведомление в Telegram.
    """
    bans = set()
    try:
        with open(LOG_FILE) as f:
            for line in f:
                if "Ban" in line:
                    ip_match = re.search(r"Ban (\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        ip = ip_match.group(1)
                        bans.add(ip)
                        await save_ban(ip)
    except Exception as e:
        print("Fail2ban error:", e)

    return {"banned_ips": list(bans)}


async def save_ban(ip: str):
    """
    Сохраняет бан в БД, если его ещё нет.
    Отправляет уведомление в Telegram.
    """
    async with AsyncSessionLocal() as db:

        try:
            result = await db.execute(
                select(Ban).filter(Ban.ip == ip)
            )
            existing = result.scalars().first()

            if existing:
                return
            

            new_ban = Ban(ip=ip)
            db.add(new_ban)
            await db.commit()

            # --- уведомление в Telegram ---
            await notify(f"⚠ Новый бан: {ip}")

        except Exception as e:
            await db.rollback()
            print("DB Error:", e)


async def unban_ip(ip: str):
    """
    Разбанивает IP через fail2ban и обновляет БД
    """
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return {"error": "Invalid IP"}

    async with AsyncSessionLocal() as db:

        try:
            result = await db.execute(
                select(Ban).filter(Ban.ip == ip, Ban.status == "banned")
            )
            ban = result.scalars().first()

            if not ban:
                return {"error": "IP not found or already unbanned"}

            result = subprocess.run(
                ["sudo", "fail2ban-client", "set", "sshd", "unbanip", ip],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {"error": result.stderr or result.stdout or "fail2ban error"}

            ban.status = "unbanned"
            ban.unbanned_at = datetime.now(timezone.utc)

            await db.commit()
            return {"status": "unbanned", "ip": ip}

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


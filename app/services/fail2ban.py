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

async def process_fail2ban_event(ip: str, action: str):
    async with AsyncSessionLocal() as db: #connect

        try:
            #SEARCH Ban on DB
            result = await db.execute(select(Ban).filter(Ban.ip == ip))
            record = result.scalars().first()

            new_status = "banned" if action == "Ban" else "unbanned"

            if not record:
                if action == "Unban": return 

                record = Ban(ip=ip, status=new_status)
                db.add(record)
                await db.commit()
                await notify(f"Warning: Ip {ip} block")

            else:
                if record.status != new_status:
                    record.status = new_status

                    await db.commit()

                    msg= f"IP {ip} y blocked" if action == "Ban" else f"IP {ip} unblock"
                    await notify(msg)

        except Exception as e:
            await db.rollback()
            print(f"Error {ip}: {e}")


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


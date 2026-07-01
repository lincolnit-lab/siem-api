import re
import ipaddress
import subprocess
import asyncio
import aiofiles
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db.models import Ban
from dotenv import load_dotenv
import os
from bot.telegram_bot import notify  # асинхронная функция для Telegram

LOG_FILE = os.getenv("LOG_FILE_FAIL2BAN")
PIPE_FILE = "/var/log/siem_unban.pipe"

async def watch_log_file():
    """
    Асинхронный воркер с защитой от ротации (Log Rotation Immune).
    При старте прыгает в конец, при ротации — читает новый файл с самого начала (0).
    """
    print(f"[*] Запущен защищенный мониторинг лога: {LOG_FILE}")
    
    # Флаг первого запуска системы
    first_run = True
    
    while True:
        try:
            if not os.path.exists(LOG_FILE):
                print(f"[-] Предупреждение: Файл {LOG_FILE} не найден. Ожидание появления...")
                await asyncio.sleep(5)
                continue

            current_inode = os.stat(LOG_FILE).st_ino
            
            async with aiofiles.open(LOG_FILE, mode='r', encoding='utf-8', errors='ignore') as f:
                
                if first_run:
                    # ТОЛЬКО ПРИ ПЕРВОМ СТАРТЕ: игнорируем терабайты старой истории
                    await f.seek(0, os.SEEK_END)
                    print(f"[+] Холодный старт. Курсор смещен в конец файла. Inode: {current_inode}")
                    first_run = False  # Сбрасываем флаг навсегда
                else:
                    # ПРИ РОТАЦИИ: читаем новый файл с самого первого байта (0), не теряя ни единой строки!
                    print(f"[+] Обнаружен новый лог после ротации. Читаем с позиции 0. Inode: {current_inode}")
                
                rotation_detected = False
                
                while not rotation_detected:
                    line = await f.readline()
                    
                    if not line:
                        await asyncio.sleep(1)
                        
                        try:
                            if os.path.exists(LOG_FILE):
                                disk_inode = os.stat(LOG_FILE).st_ino
                                if disk_inode != current_inode:
                                    print(f"[!] ВНИМАНИЕ: Обнаружена ротация! Старый inode: {current_inode}, Новый: {disk_inode}")
                                    rotation_detected = True
                        except Exception as stat_err:
                            print(f"[-] Ошибка проверки статуса файла при ротации: {stat_err}")
                        
                        continue
                    
                    if "Ban" in line:
                        ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line)
                        if ip_match:
                            ip = ip_match.group(0)
                            print(f"[!] Обнаружен новый бан в логе: {ip}")
                            await save_ban(ip)
                            
        except Exception as e:
            print(f"[-] Критическая ошибка воркера fail2ban: {e}. Перезапуск через 5 секунд...")
            await asyncio.sleep(5)

            
async def save_ban(ip: str):
    """Сохраняет бан в БД (если уникальный) и отправляет алерт"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Ban).filter(Ban.ip == ip))
            existing = result.scalars().first()

            if existing:
                return

            new_ban = Ban(ip=ip, status="banned")
            db.add(new_ban)
            await db.commit()

            # Мгновенный алерт администратору
            await notify(f"⚠ **SIEM ALERT**: Обнаружен новый бан IP: `{ip}`")
        except Exception as e:
            await db.rollback()
            print("[-] Ошибка сохранения бана в БД:", e)


async def unban_ip(ip: str):
    """
    Разбанивает IP: меняет статус в БД и отправляет команду на хост через Named Pipe.
    """
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return {"error": "Invalid IP address format"}

    async with AsyncSessionLocal() as db:
        try:
            # 1. Проверяем, есть ли активный бан в БД
            result = await db.execute(
                select(Ban).filter(Ban.ip == ip, Ban.status == "banned")
            )
            ban = result.scalars().first()

            if not ban:
                return {"error": "IP not found in database or already unbanned"}

            # 2. Пишем IP в именованный пайп для хоста (используем aiofiles для асинхронности)
            if os.path.exists(PIPE_FILE):
                async with aiofiles.open(PIPE_FILE, mode='w') as pipe:
                    await pipe.write(f"{ip}\n")
                print(f"[+] Команда unban для {ip} успешно отправлена в Named Pipe")
            else:
                return {"error": "SIEM Unban Pipe не найден. Проверьте настройки хоста."}

            # 3. Обновляем статус в базе данных логов
            ban.status = "unbanned"
            ban.unbanned_at = datetime.now()
            await db.commit()

            return {"status": "unbanned", "ip": ip}

        except Exception as e:
            await db.rollback()
            print(f"[-] Ошибка при анбане IP {ip}: {e}")
            return {"error": str(e)}
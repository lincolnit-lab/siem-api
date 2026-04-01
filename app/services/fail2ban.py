import re
from app.db.database import SessionLocal
from app.db.models import Ban
import subprocess
import ipaddress
from datetime import datetime, timezone


def get_bans():
    bans = set()

    try:
        with open("/var/log/fail2ban.log") as f:
            for line in f:
                if "Ban" in line:
                    ip_match = re.search(r"Ban (\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        ip = ip_match.group(1)
                        bans.add(ip)
                        save_ban(ip)

    except Exception as e:
        return {"error": str(e)}

    return {"banned_ips": list(bans)}


def save_ban(ip: str):
    db = SessionLocal()
    try:
        existing = db.query(Ban).filter(
            Ban.ip == ip,
            Ban.status == "banned"
        ).first()

        if existing:
            return
        
        ban = Ban(ip=ip)
        db.add(ban)
        db.commit()

    finally:
        db.close()


def unban_ip(ip: str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return {"error": "Invalid IP"}
    
    db = SessionLocal()
    try:
        ban = db.query(Ban).filter(
            Ban.ip == ip,
            Ban.status == "banned"
        ).first()

        if not ban:
            return {"error": "Ip not found or already unbanned"}

        result = subprocess.run(
            ["sudo","fail2ban-client", "set", "sshd", "unbanip", ip],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {"error": result.stderr or result.stdout or "fail2ban error"}
        
        ban.status = "unbanned"
        ban.unbanned_at = datetime.now(timezone.utc)

        db.commit()


        return {"status": "unbanned", "ip": ip}
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    
    finally:
        db.close()
        
import re
from app.db.database import SessionLocal
from app.db.models import Ban
import subprocess

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
        ban = Ban(ip=ip)
        db.add(ban)
        db.commit()
    finally:
        db.close()


def unban_ip(ip: str):
    try:
        result = subprocess.run(
            ["fail2ban-client", "set", "sshd", "unbanip", ip],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {"error": result.stderr}
        
        return {"status": "unbanned", "ip": ip}
    
    except Exception as e:
        return {"error": str(e)}
import re 

def get_bans():
    bans = []

    try:
        with open("/var/log/fail2ban.log") as f:
            for line in f:
                if "Ban" in line:
                    ip_match =re.search(r"Ban (\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        bans.append(ip_match.group(1))

    except Exception as e:
        return {"error": str(e)}
    
    return {"banned_ips": bans}
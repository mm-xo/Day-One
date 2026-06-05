from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def get_utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_local_today_iso(timezone_name: str, now_utc: datetime | None = None):
    try:
        user_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Invalid timezone: {timezone_name}")
    
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    
    local_now = now_utc.astimezone(user_timezone)
    
    return local_now.date().isoformat()
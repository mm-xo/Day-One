from datetime import datetime, timezone

def get_utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

# TODO implement local_day logic, and other functions related to user's time
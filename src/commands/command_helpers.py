# import discord
from datetime import datetime, timezone

def get_utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def validate_role(member, accepted_roles):
    roles = member.roles # list of roles
    for role in roles:
        if role.name in accepted_roles:
            return True
    return False
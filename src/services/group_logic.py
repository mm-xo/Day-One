import re

GROUP_NAME_RE = re.compile(r"^[A-Z0-9](?:[A-Z0-9 _-]*[A-Z0-9])?$")

def normalize_group_name(name: str) -> str:
    return " ".join(name.strip().split()).upper()

def is_valid_allowed_skip_days(days: int) -> bool:
    return 0 <= days <= 7

def is_valid_group_name(name: str) -> bool:
    normalized = normalize_group_name(name)
    
    if len(normalized) < 2:
        return False
    
    if len(normalized) > 16:
        return False
    
    if not GROUP_NAME_RE.fullmatch(normalized):
        return False
    
    return True
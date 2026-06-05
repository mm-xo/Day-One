
def normalize_group_name(name: str) -> str:
    return name.strip().upper()

def is_valid_allowed_skip_days(days: int) -> bool:
    return 0 <= days <= 7

def is_valid_group_name(name: str) -> bool:
    normalized = normalize_group_name(name)
    
    if len(normalized) < 2:
        return False
    
    if len(normalized) > 16:
        return False
    
    return True
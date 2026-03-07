from dateutil.parser import parse
from datetime import datetime

def to_iso_date(date_input):
    
    if isinstance(date_input, datetime):
        return date_input.isoformat()
    elif isinstance(date_input, str):
        try:
            dt = parse(date_input)
            return dt.isoformat()
        except (ValueError, OverflowError):
            raise ValueError(f"Cannot parse '{date_input}' as a valid date.")
    else:
        raise TypeError("Input must be a string or datetime object.")
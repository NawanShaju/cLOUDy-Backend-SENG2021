from dateutil.parser import parse
from datetime import datetime
from uuid import UUID
from app.services.email.email_services import EmailPayload
import json

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

def is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
    
def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except (ValueError, TypeError) as e:
        return False
    return True

def parse_email_request(data: dict) -> tuple[EmailPayload | None, str | None]:
    required_fields = ["to", "subject", "body"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"
 
    to = data["to"]
    if isinstance(to, str):
        to = [to]
        
    if not isinstance(to, list) or not all(isinstance(r, str) for r in to):
        return None, "'to' must be a string or list of strings."
 
    payload = EmailPayload(
        to=to,
        subject=data["subject"],
        body=data["body"],
        sender=data.get("sender"),
        cc=data.get("cc"),
        bcc=data.get("bcc"),
        html_body=data.get("html_body"),
        attachments=data.get("attachments", []),
    )
    
    return payload, None
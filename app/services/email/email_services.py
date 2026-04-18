import smtplib
import base64
from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from .email_style import generate_default_html
import os

env = Environment(loader=FileSystemLoader("templates"))

load_dotenv()

@dataclass
class EmailPayload:
    to: list[str]
    subject: str
    body: str
    sender: Optional[str] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    html_body: Optional[str] = None
    attachments: Optional[list[dict]] = field(default_factory=list)
    # attachment format: [{"filename": "file.txt", "data": "<base64-encoded string>"}]
    
def render_email_template(data: dict) -> str:
    template = env.get_template("cloudy_email.html")

    return template.render(
        title=data["title"],
        message=data["message"],
        order_id=data.get("order_id"),
        status=data.get("status"),
        delivery_date=data.get("delivery_date"),
    )


def build_email(payload: EmailPayload) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = payload.subject
    msg["From"] = payload.sender or os.environ.get("SMTP_SENDER", "noreply@example.com")
    msg["To"] = ", ".join(payload.to)
 
    if payload.cc:
        msg["Cc"] = ", ".join(payload.cc)
 
    if payload.bcc:
        msg["Bcc"] = ", ".join(payload.bcc)
 
    body_part = MIMEMultipart("alternative")
    body_part.attach(MIMEText(payload.body, "plain"))
    if payload.html_body:
        html_content = payload.html_body
    else:
        html_content = generate_default_html(payload)
        
    body_part.attach(MIMEText(html_content, "html"))
        
    msg.attach(body_part)
 
    for attachment in payload.attachments or []:
        part = MIMEBase("application", "octet-stream")
        raw_data = attachment["data"]
        if isinstance(raw_data, str):
            raw_data = base64.b64decode(raw_data)
        part.set_payload(raw_data)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{attachment["filename"]}"',
        )
        msg.attach(part)
 
    return msg


def send_email(payload: EmailPayload) -> dict:
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    try:
        msg = build_email(payload)

        all_recipients = list(payload.to)
        if payload.cc:
            all_recipients += payload.cc
        if payload.bcc:
            all_recipients += payload.bcc

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(msg["From"], all_recipients, msg.as_string())

        return {"success": True, "message": f"Email sent to {', '.join(payload.to)}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD."}
    except smtplib.SMTPConnectError:
        return {"success": False, "message": f"Could not connect to SMTP server at {smtp_host}:{smtp_port}."}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
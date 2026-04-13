"""Email send/receive for nekonote scripts.

Usage::

    from nekonote import mail

    mail.send(to=["user@example.com"], subject="Done", body="RPA finished.")
    messages = mail.receive(imap_server="imap.gmail.com", username="...", password="...")
"""

from __future__ import annotations

import email
import email.utils
import imaplib
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


def send(
    *,
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[str] | None = None,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    username: str = "",
    password: str = "",
    use_tls: bool = True,
) -> None:
    """Send an email via SMTP."""
    msg = MIMEMultipart()
    msg["From"] = username
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachments or []:
        p = Path(path)
        with open(p, "rb") as f:
            part = MIMEApplication(f.read(), Name=p.name)
        part["Content-Disposition"] = f'attachment; filename="{p.name}"'
        msg.attach(part)

    recipients = list(to) + (cc or []) + (bcc or [])

    with smtplib.SMTP(smtp_server, smtp_port) as srv:
        if use_tls:
            srv.starttls()
        if username and password:
            srv.login(username, password)
        srv.sendmail(username, recipients, msg.as_string())


def receive(
    *,
    imap_server: str = "imap.gmail.com",
    imap_port: int = 993,
    username: str = "",
    password: str = "",
    folder: str = "INBOX",
    filter_subject: str = "",
    unread_only: bool = True,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Receive emails via IMAP.

    Returns list of dicts with: subject, from, date, body, attachments.
    """
    conn = imaplib.IMAP4_SSL(imap_server, imap_port)
    conn.login(username, password)
    conn.select(folder)

    criteria = "UNSEEN" if unread_only else "ALL"
    if filter_subject:
        criteria = f'(SUBJECT "{filter_subject}"' + (' UNSEEN)' if unread_only else ')')

    _, msg_ids = conn.search(None, criteria)
    ids = msg_ids[0].split()
    if limit:
        ids = ids[-limit:]

    messages = []
    for mid in ids:
        _, data = conn.fetch(mid, "(RFC822)")
        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        body_text = ""
        attachments = []
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_text += payload.decode(charset, errors="replace")
            elif "attachment" in cd:
                filename = part.get_filename() or "attachment"
                attachments.append({"filename": filename, "size": len(part.get_payload(decode=True) or b"")})

        messages.append({
            "subject": str(email.header.make_header(email.header.decode_header(msg.get("Subject", "")))),
            "from": msg.get("From", ""),
            "date": msg.get("Date", ""),
            "body": body_text.strip(),
            "attachments": attachments,
        })

    conn.logout()
    return messages


def send_outlook(
    *,
    to: list[str],
    subject: str = "",
    body: str = "",
    attachments: list[str] | None = None,
) -> None:
    """Send email via Outlook COM (Windows only)."""
    import win32com.client

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail_item = outlook.CreateItem(0)
    mail_item.To = "; ".join(to)
    mail_item.Subject = subject
    mail_item.Body = body
    for path in attachments or []:
        mail_item.Attachments.Add(str(Path(path).resolve()))
    mail_item.Send()

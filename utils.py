import os
import pickle
import re
from typing import Dict
from email.mime.text import MIMEText
import base64

import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()


def get_credentials():
    """Load OAuth credentials and return an authorized Credentials object."""
    scopes = os.getenv("SCOPES", "").split()
    creds = None
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("CREDENTIALS_FILE"), scopes
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "wb") as token:
            pickle.dump(creds, token)
    return creds


def get_unique_senders(service) -> Dict[str, Dict[str, int]]:
    """Return mapping of sender email to name and message count."""
    senders: Dict[str, Dict[str, int]] = {}
    next_page = None
    while True:
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["CATEGORY_PROMOTIONS"], pageToken=next_page)
            .execute()
        )
        for msg in results.get("messages", []):
            msg_data = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata")
                .execute()
            )
            headers = msg_data.get("payload", {}).get("headers", [])
            from_header = next(
                (h["value"] for h in headers if h["name"].lower() == "from"), None
            )
            if from_header:
                email_start = from_header.find("<")
                email_end = from_header.find(">")
                if email_start != -1 and email_end != -1:
                    sender = from_header[email_start + 1 : email_end]
                    name = from_header[:email_start].strip().strip('"')
                else:
                    sender = from_header
                    name = ""
                info = senders.get(sender, {"name": name, "count": 0})
                if not info["name"]:
                    info["name"] = name
                info["count"] += 1
                senders[sender] = info
        next_page = results.get("nextPageToken")
        if not next_page:
            break
    return senders


def create_filter(service, sender: str):
    """Create a Gmail filter that trashes mail from the provided sender."""
    filter_obj = {
        "criteria": {"from": sender},
        "action": {"addLabelIds": ["TRASH"]},
    }
    service.users().settings().filters().create(userId="me", body=filter_obj).execute()


def delete_emails_from_sender(service, sender: str):
    """Delete existing messages from a sender in the Promotions category."""
    query = f"from:{sender} label:CATEGORY_PROMOTIONS"
    message_ids = []
    next_page = None
    while True:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=next_page)
            .execute()
        )
        message_ids.extend([msg["id"] for msg in results.get("messages", [])])
        next_page = results.get("nextPageToken")
        if not next_page:
            break
    if message_ids:
        body = {
            "ids": message_ids,
            "removeLabelIds": ["INBOX", "CATEGORY_PROMOTIONS"],
            "addLabelIds": ["TRASH"],
        }
        service.users().messages().batchModify(userId="me", body=body).execute()


def _send_unsubscribe_email(service, mailto_link: str):
    """Send an unsubscribe email based on a mailto link."""
    from urllib.parse import urlsplit, parse_qs

    parsed = urlsplit(mailto_link)
    to_addr = parsed.path
    subject = parse_qs(parsed.query).get("subject", ["unsubscribe"])[0]
    message = MIMEText("")
    message["to"] = to_addr
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def unsubscribe_sender(service, sender: str) -> bool:
    """Attempt to unsubscribe from a sender using the List-Unsubscribe header."""
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=f"from:{sender}", maxResults=1)
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            return False
        msg_id = messages[0]["id"]
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        unsub = next(
            (h["value"] for h in headers if h["name"].lower() == "list-unsubscribe"),
            None,
        )
        if not unsub:
            return False
        mailto_match = re.search(r"<mailto:([^>]+)>", unsub)
        if mailto_match:
            _send_unsubscribe_email(service, mailto_match.group(1))
            return True
        url_match = re.search(r"<(https?://[^>]+)>", unsub)
        if url_match:
            try:
                requests.get(url_match.group(1), timeout=10)
                return True
            except Exception:
                return False
    except HttpError:
        pass
    return False


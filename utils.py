import os
import pickle
from typing import Set
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


def get_unique_senders(service) -> Set[str]:
    """Return a set of unique sender addresses from the Promotions category."""
    senders: Set[str] = set()
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
                else:
                    sender = from_header
                senders.add(sender)
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


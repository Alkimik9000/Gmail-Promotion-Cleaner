import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

import config
import utils

load_dotenv()


def main():
    creds = utils.get_credentials()
    service = build("gmail", "v1", credentials=creds)

    senders = utils.get_unique_senders(service)
    print(f"Found {len(senders)} unique senders in Promotions.")

    senders = list(senders)[: config.MAX_SENDERS]
    print(f"Processing {len(senders)} senders (limited by config).")

    for sender in senders:
        try:
            utils.create_filter(service, sender)
            utils.delete_emails_from_sender(service, sender)
            print(f"Processed sender: {sender}")
        except Exception as e:
            print(f"Error processing {sender}: {e}")


if __name__ == "__main__":
    main()


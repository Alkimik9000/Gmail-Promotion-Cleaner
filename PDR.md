# Project Design Requirements (PDR) for Gmail Promotions Cleaner

## Overview
This project provides a Python application with a Tkinter GUI that automates removing promotional email from Gmail. It identifies unique senders from the Promotions tab, lets the user select which senders to act on, and can either create filters to trash future mail or attempt to unsubscribe via the `List-Unsubscribe` header before deleting existing conversations.

## Requirements
### Functional Requirements
1. Authenticate with the Gmail API using OAuth 2.0.
2. Fetch all emails labeled `CATEGORY_PROMOTIONS`.
3. Extract unique sender addresses from the `From` header.
4. For each unique sender:
   - Optionally create a Gmail filter that moves future mail from that sender to the Trash.
   - Optionally attempt to unsubscribe from the sender using any `List-Unsubscribe` header.
   - Delete existing mail from that sender.
5. Use batch operations to minimize API calls.
6. Limit processing to a configurable maximum number of senders (Gmail supports 1000 filters).

### Non-Functional Requirements
1. **Security** – store sensitive data in environment variables and rely on Google's OAuth flow.
2. **Performance** – batch API requests when possible.
3. **Error Handling** – log and skip failures without aborting the entire run.
4. **Dependencies** – rely on Google API client libraries, `python-dotenv` and `requests`.
5. **Environment** – Python 3.8 or newer.

## Architecture
- `main.py` – orchestrates the overall process.
- `utils.py` – helper functions for Gmail API operations.
- `config.py` – configuration constants such as the sender limit.
- `.env` (or `.env.example`) – environment variables including OAuth scopes and credentials path.

## Assumptions
- The user has enabled the Gmail API and downloaded the credentials JSON file.
- Deleted messages first go to the Trash and are permanently removed after 30 days.
- No AI integration in the base version.

## Risks
- Hitting Gmail API rate limits. Retry or continue when errors occur.
- Approaching Gmail's filter limit (1000). `MAX_SENDERS` controls this.
- Accidental data loss. Users should run the tool carefully and ideally test in a secondary account.

## Setup Instructions
See `README.md` for detailed setup and usage steps.

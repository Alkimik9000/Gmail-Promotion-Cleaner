# Gmail Promotions Cleaner

This project now provides a simple GUI application for cleaning promotional email in Gmail. It scans the Promotions category to gather unique senders and lets you choose which ones to process. You can either create filters that trash future mail from them or attempt to unsubscribe using the `List-Unsubscribe` header and then delete their messages.

## Prerequisites
- Python 3.8+
- Google Cloud project with the Gmail API enabled
- OAuth credentials file (`credentials.json`)

## Installation
1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd gmail-promotions-cleaner
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and adjust paths or scopes if needed. Place your `credentials.json` in the project root. The scopes include Gmail send access for unsubscribe emails.

## Usage
Run the application from the project directory:
```bash
python main.py
```
On first run a browser will open for OAuth authentication. After authorizing, a window appears listing senders from your Promotions tab. Select any number of senders and click **Unsubscribe and Delete** or **Filter and Delete**. A `token.json` file stores your credentials for next time.

## Configuration
`config.py` defines `MAX_SENDERS` – the maximum number of unique senders to process. Gmail allows up to 1000 filters, so keep this number at or below that limit.

## Warnings
- **Data loss**: deleted messages go to Trash and will be permanently removed after 30 days. Test on a small set or a non-primary account.
- **Filter limit**: Gmail has a limit of ~1000 filters. The script stops once it has created filters for `MAX_SENDERS` senders.

## License
MIT

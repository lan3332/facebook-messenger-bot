# facebook-messenger-bot

A Flask-based Facebook Messenger bot that handles user support queries — including payment verification and Visual Studio Code extension licensing issues.

## Features

- Webhook verification for Facebook Messenger
- Detects messages about payment + VS Code "update required" issues (Spanish & English)
- Responds with step-by-step instructions to re-activate a purchased VS Code extension

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export PAGE_ACCESS_TOKEN=<your_facebook_page_access_token>
   export VERIFY_TOKEN=<your_chosen_verify_token>
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Expose the `/webhook` endpoint (e.g. via ngrok) and register it in your Facebook App dashboard using the same `VERIFY_TOKEN`.

## Running Tests

```bash
pytest test_app.py -v
```

## Payment / VS Code Update Issue

When a user sends a message indicating they made a payment but still see an "update" prompt in Visual Studio Code, the bot automatically replies with:

1. Uninstall the extension from VS Code.
2. Restart VS Code.
3. Reinstall the extension from the Marketplace.
4. Sign in with the account linked to the purchase.
5. If the problem persists, contact support with the purchase email for manual license activation.

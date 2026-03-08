import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")

# Keywords that indicate payment/VS Code licensing issues (Spanish and English)
PAYMENT_KEYWORDS = [
    "pago", "pague", "realice mi pago", "ya pague", "compre", "compré",
    "payment", "paid", "purchase",
]
VSCODE_KEYWORDS = [
    "visual code", "visual studio code", "vscode", "vs code",
    "extension", "extensión",
]
UPDATE_KEYWORDS = [
    "actualizar", "update", "upgrade", "actualización",
]

SPANISH_MARKERS = [
    "ya", "pague", "pago", "pero", "puedo", "usar", "sale", "realice",
    "actualizar", "extensión", "me", "es",
]

PAYMENT_VSCODE_RESPONSE_ES = (
    "Entendemos que ya realizaste tu pago. Para resolver el problema de "
    "activación en Visual Studio Code, sigue estos pasos:\n\n"
    "1. Abre Visual Studio Code.\n"
    "2. Ve a la pestaña de Extensiones (Ctrl+Shift+X).\n"
    "3. Busca la extensión y haz clic en 'Desinstalar'.\n"
    "4. Reinicia VS Code.\n"
    "5. Vuelve a instalar la extensión desde el Marketplace.\n"
    "6. Inicia sesión con la cuenta asociada a tu compra.\n\n"
    "Si el problema persiste, comparte el correo electrónico con el que "
    "realizaste tu pago y te ayudaremos a activar tu licencia manualmente."
)

PAYMENT_VSCODE_RESPONSE_EN = (
    "We understand that you have already made your payment. To resolve the "
    "activation issue in Visual Studio Code, please follow these steps:\n\n"
    "1. Open Visual Studio Code.\n"
    "2. Go to the Extensions tab (Ctrl+Shift+X).\n"
    "3. Find the extension and click 'Uninstall'.\n"
    "4. Restart VS Code.\n"
    "5. Reinstall the extension from the Marketplace.\n"
    "6. Sign in with the account linked to your purchase.\n\n"
    "If the issue persists, please share the email address used for payment "
    "and we will activate your license manually."
)

DEFAULT_RESPONSE = (
    "Hola! ¿En qué te podemos ayudar? Si tienes problemas con tu compra o "
    "con Visual Studio Code, escríbenos los detalles.\n\n"
    "Hello! How can we help you? If you have issues with your purchase or "
    "Visual Studio Code, please write us the details."
)


def _text_contains_any(text, keywords):
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def classify_message(text):
    """Return 'payment_vscode' if the message is about a payment + VS Code
    update issue, otherwise return 'default'."""
    has_payment = _text_contains_any(text, PAYMENT_KEYWORDS)
    has_vscode = _text_contains_any(text, VSCODE_KEYWORDS)
    has_update = _text_contains_any(text, UPDATE_KEYWORDS)

    if has_payment and (has_vscode or has_update):
        return "payment_vscode"
    if has_vscode and has_update:
        return "payment_vscode"
    return "default"


def _is_spanish(text):
    """Return True if the text appears to be Spanish."""
    text_lower = text.lower()
    return any(word in text_lower.split() for word in SPANISH_MARKERS)


def build_reply(text):
    """Return the appropriate reply message for the given user text."""
    intent = classify_message(text)
    if intent == "payment_vscode":
        if _is_spanish(text):
            return PAYMENT_VSCODE_RESPONSE_ES
        return PAYMENT_VSCODE_RESPONSE_EN
    return DEFAULT_RESPONSE


def send_message(recipient_id, message_text):
    """Send a text message back to the user via the Messenger Send API."""
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps(
        {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
        }
    )
    url = "https://graph.facebook.com/v18.0/me/messages"
    response = requests.post(url, params=params, headers=headers, data=data, timeout=10)
    return response


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Handle the Facebook webhook verification challenge."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Receive and process Messenger events."""
    data = request.get_json(silent=True)

    if not data or data.get("object") != "page":
        return "Not a page event", 400

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event.get("sender", {}).get("id")
            if not sender_id:
                continue

            message = messaging_event.get("message", {})
            text = message.get("text", "")

            if text:
                reply = build_reply(text)
                if PAGE_ACCESS_TOKEN:
                    send_message(sender_id, reply)

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

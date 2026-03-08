import pytest
from app import app, classify_message, build_reply, PAYMENT_VSCODE_RESPONSE_ES, PAYMENT_VSCODE_RESPONSE_EN, DEFAULT_RESPONSE


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# classify_message tests
# ---------------------------------------------------------------------------

class TestClassifyMessage:
    def test_spanish_payment_vscode_update(self):
        assert classify_message("ya realice mi pago pero no puedo usar en visual code me sale actualizar") == "payment_vscode"

    def test_spanish_payment_vscode(self):
        assert classify_message("ya pague y no funciona en visual studio code") == "payment_vscode"

    def test_english_payment_vscode(self):
        assert classify_message("I already paid but VS Code shows update") == "payment_vscode"

    def test_vscode_update_without_payment(self):
        # VS Code + update keywords alone should also trigger payment_vscode intent
        assert classify_message("visual code me pide actualizar") == "payment_vscode"

    def test_unrelated_message(self):
        assert classify_message("hola, cómo estás?") == "default"

    def test_only_payment_keyword(self):
        # payment alone (no VS Code or update) → default
        assert classify_message("ya realice mi pago") == "default"

    def test_case_insensitive(self):
        assert classify_message("PAGO Visual Code ACTUALIZAR") == "payment_vscode"


# ---------------------------------------------------------------------------
# build_reply tests
# ---------------------------------------------------------------------------

class TestBuildReply:
    def test_payment_vscode_returns_spanish_guide(self):
        reply = build_reply("ya realice mi pago pero no puedo usar en visual code me sale actualizar")
        assert reply == PAYMENT_VSCODE_RESPONSE_ES

    def test_payment_vscode_returns_english_guide(self):
        reply = build_reply("I already paid but VS Code shows update")
        assert reply == PAYMENT_VSCODE_RESPONSE_EN

    def test_default_returns_default_response(self):
        reply = build_reply("hola")
        assert reply == DEFAULT_RESPONSE


# ---------------------------------------------------------------------------
# Webhook endpoint tests
# ---------------------------------------------------------------------------

class TestWebhook:
    def test_verify_webhook_success(self, client):
        response = client.get(
            "/webhook",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": "my_verify_token",
                "hub.challenge": "challenge_code_123",
            },
        )
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "challenge_code_123"

    def test_verify_webhook_wrong_token(self, client):
        response = client.get(
            "/webhook",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_code_123",
            },
        )
        assert response.status_code == 403

    def test_handle_webhook_non_page_event(self, client):
        response = client.post(
            "/webhook",
            json={"object": "other"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_handle_webhook_valid_page_event(self, client):
        payload = {
            "object": "page",
            "entry": [
                {
                    "messaging": [
                        {
                            "sender": {"id": "user123"},
                            "message": {
                                "text": "ya realice mi pago pero visual code me pide actualizar"
                            },
                        }
                    ]
                }
            ],
        }
        response = client.post("/webhook", json=payload, content_type="application/json")
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "ok"

    def test_handle_webhook_no_text_message(self, client):
        payload = {
            "object": "page",
            "entry": [
                {
                    "messaging": [
                        {
                            "sender": {"id": "user123"},
                            "message": {},
                        }
                    ]
                }
            ],
        }
        response = client.post("/webhook", json=payload, content_type="application/json")
        assert response.status_code == 200

"""
Test WhatsApp / Inbox router + service.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_CONV = {
    "id": "conv-1",
    "phone": "+393331234567",
    "leadId": "lead-1",
    "leadName": "Mario Rossi",
    "status": "open",
    "unreadCount": 2,
    "lastMessageAt": "2026-01-20T10:00:00Z",
}

_MSG_OUT = {
    "id": "msg-1",
    "conversationId": "conv-1",
    "direction": "outbound",
    "body": "Ciao Mario",
    "status": "sent",
}

_MSG_IN = {
    "id": "msg-2",
    "conversationId": "conv-1",
    "direction": "inbound",
    "body": "Salve",
    "status": "received",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_list_conversations():
    with patch(
        "app.routers.whatsapp.whatsapp_service.list_conversations",
        new_callable=AsyncMock,
        return_value=[_CONV],
    ):
        resp = client.get("/api/v1/whatsapp/conversations")
    assert resp.status_code == 200
    assert resp.json()[0]["phone"] == "+393331234567"


def test_get_conversation_not_found():
    with patch(
        "app.routers.whatsapp.whatsapp_service.get_conversation",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/api/v1/whatsapp/conversations/missing")
    assert resp.status_code == 404


def test_create_conversation():
    with patch(
        "app.routers.whatsapp.whatsapp_service.create_conversation",
        new_callable=AsyncMock,
        return_value=_CONV,
    ):
        resp = client.post(
            "/api/v1/whatsapp/conversations",
            json={"phone": "+39 333 1234567", "leadId": "lead-1", "leadName": "Mario Rossi"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_list_messages():
    with patch(
        "app.routers.whatsapp.whatsapp_service.list_messages",
        new_callable=AsyncMock,
        return_value=[_MSG_OUT, _MSG_IN],
    ):
        resp = client.get("/api/v1/whatsapp/conversations/conv-1/messages")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_send_message():
    with patch(
        "app.routers.whatsapp.whatsapp_service.send_message",
        new_callable=AsyncMock,
        return_value=_MSG_OUT,
    ):
        resp = client.post(
            "/api/v1/whatsapp/conversations/conv-1/messages",
            json={"body": "Ciao Mario"},
        )
    assert resp.status_code == 200
    assert resp.json()["direction"] == "outbound"


def test_send_message_not_found():
    with patch(
        "app.routers.whatsapp.whatsapp_service.send_message",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.post(
            "/api/v1/whatsapp/conversations/missing/messages",
            json={"body": "x"},
        )
    assert resp.status_code == 404


def test_mark_read_and_close():
    with patch(
        "app.routers.whatsapp.whatsapp_service.mark_read",
        new_callable=AsyncMock,
        return_value={**_CONV, "unreadCount": 0},
    ):
        resp = client.post("/api/v1/whatsapp/conversations/conv-1/read")
    assert resp.status_code == 200
    assert resp.json()["unreadCount"] == 0

    with patch(
        "app.routers.whatsapp.whatsapp_service.close_conversation",
        new_callable=AsyncMock,
        return_value={**_CONV, "status": "closed"},
    ):
        resp = client.post("/api/v1/whatsapp/conversations/conv-1/close")
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_inbox_stats():
    stats = {"totalConversations": 3, "openConversations": 2, "unreadMessages": 5}
    with patch(
        "app.routers.whatsapp.whatsapp_service.inbox_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = client.get("/api/v1/whatsapp/stats")
    assert resp.status_code == 200
    assert resp.json()["unreadMessages"] == 5


def test_webhook_inbound_simple():
    with patch(
        "app.routers.whatsapp.whatsapp_service.receive_inbound",
        new_callable=AsyncMock,
        return_value={"conversation": _CONV, "message": _MSG_IN},
    ):
        resp = client.post(
            "/api/v1/whatsapp/webhook",
            json={"phone": "+393331234567", "body": "Salve"},
        )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_webhook_inbound_meta_envelope():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "393331234567",
                                    "id": "wamid.1",
                                    "text": {"body": "Buongiorno"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    with patch(
        "app.routers.whatsapp.whatsapp_service.receive_inbound",
        new_callable=AsyncMock,
        return_value={"conversation": _CONV, "message": _MSG_IN},
    ) as recv:
        resp = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert resp.status_code == 200
    recv.assert_awaited_once()
    assert recv.call_args.args[0] == "393331234567"
    assert recv.call_args.args[1] == "Buongiorno"


def test_webhook_verify():
    resp = client.get(
        "/api/v1/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "aichain-wa-verify",
            "hub.challenge": "12345",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == 12345


# ── service unit ────────────────────────────────────────────────

def test_normalize_phone():
    from app.services.whatsapp_service import normalize_phone

    assert normalize_phone("333 123.4567") == "+3331234567"
    assert normalize_phone("+393331234567") == "+393331234567"
    assert normalize_phone("") == ""


@pytest.mark.asyncio
async def test_receive_inbound_creates_conversation():
    from app.services import whatsapp_service

    mock_col_conv = MagicMock()
    mock_col_conv.find_one = AsyncMock(return_value=None)
    mock_col_conv.insert_one = AsyncMock()
    mock_col_conv.update_one = AsyncMock()

    mock_col_msg = MagicMock()
    mock_col_msg.insert_one = AsyncMock()

    mock_col_leads = MagicMock()
    mock_col_leads.update_one = AsyncMock()

    mock_col_act = MagicMock()
    mock_col_act.insert_one = AsyncMock()

    def get_col(name):
        return {
            "whatsapp_conversations": mock_col_conv,
            "whatsapp_messages": mock_col_msg,
            "leads": mock_col_leads,
            "activities": mock_col_act,
        }.get(name, MagicMock())

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(side_effect=get_col)

    with patch("app.services.whatsapp_service.db", mock_db):
        result = await whatsapp_service.receive_inbound("+39 333 1112233", "Ciao")

    assert result["conversation"] is not None
    assert result["message"]["direction"] == "inbound"
    mock_col_msg.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_message_mock_mode():
    from app.services import whatsapp_service

    conv = {
        "id": "conv-1",
        "phone": "+393331234567",
        "leadId": None,
        "status": "open",
    }
    mock_col_conv = MagicMock()
    mock_col_conv.find_one = AsyncMock(return_value={**conv, "_id": "conv-1"})
    mock_col_conv.update_one = AsyncMock()

    mock_col_msg = MagicMock()
    mock_col_msg.insert_one = AsyncMock()

    def get_col(name):
        return {
            "whatsapp_conversations": mock_col_conv,
            "whatsapp_messages": mock_col_msg,
        }.get(name, MagicMock())

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(side_effect=get_col)

    with patch("app.services.whatsapp_service.db", mock_db), patch(
        "app.services.whatsapp_service.settings"
    ) as mock_settings:
        mock_settings.WHATSAPP_ACCESS_TOKEN = ""
        mock_settings.WHATSAPP_PHONE_NUMBER_ID = ""
        msg = await whatsapp_service.send_message("conv-1", "Ciao", "user_sales")

    assert msg["status"] == "sent"
    assert msg["direction"] == "outbound"
    mock_col_msg.insert_one.assert_awaited_once()

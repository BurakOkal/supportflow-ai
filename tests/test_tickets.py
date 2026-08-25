from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import Response


def ticket_payload(subject: str = "Payment was charged twice") -> dict[str, str]:
    return {
        "subject": subject,
        "description": "The same invoice was charged to my card twice.",
        "customer_email": "customer@example.com",
    }


def create_ticket(client: TestClient, subject: str = "Payment was charged twice") -> Response:
    return client.post("/api/v1/tickets", json=ticket_payload(subject))


def test_create_ticket(client: TestClient) -> None:
    response = create_ticket(client)

    assert response.status_code == 201
    body = response.json()
    assert body["subject"] == "Payment was charged twice"
    assert body["status"] == "open"
    assert body["category"] == "unclassified"
    assert body["priority"] == "unassigned"
    assert datetime.fromisoformat(body["created_at"]).tzinfo is not None
    assert datetime.fromisoformat(body["updated_at"]).tzinfo is not None


def test_create_ticket_rejects_invalid_email(client: TestClient) -> None:
    payload = ticket_payload()
    payload["customer_email"] = "not-an-email"

    response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 422


def test_list_tickets_with_pagination(client: TestClient) -> None:
    for subject in ("First ticket", "Second ticket", "Third ticket"):
        assert create_ticket(client, subject).status_code == 201

    response = client.get("/api/v1/tickets", params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["offset"] == 1
    assert response.json()["limit"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["subject"] == "Second ticket"


def test_get_ticket_by_id(client: TestClient) -> None:
    created = create_ticket(client).json()

    response = client.get(f"/api/v1/tickets/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_update_ticket(client: TestClient) -> None:
    created = create_ticket(client).json()

    response = client.patch(
        f"/api/v1/tickets/{created['id']}",
        json={"subject": "Updated payment issue", "status": "in_progress"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["subject"] == "Updated payment issue"
    assert updated["description"] == created["description"]
    assert updated["status"] == "in_progress"
    assert updated["updated_at"] != created["updated_at"]


def test_delete_ticket_and_then_return_not_found(client: TestClient) -> None:
    ticket_id = create_ticket(client).json()["id"]

    delete_response = client.delete(f"/api/v1/tickets/{ticket_id}")
    get_response = client.get(f"/api/v1/tickets/{ticket_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


def test_missing_ticket_returns_not_found_for_get_update_and_delete(
    client: TestClient,
) -> None:
    ticket_id = uuid4()

    get_response = client.get(f"/api/v1/tickets/{ticket_id}")
    update_response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "closed"},
    )
    delete_response = client.delete(f"/api/v1/tickets/{ticket_id}")

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404

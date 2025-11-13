from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.auth.models.models import User
from app.main import app


@pytest.fixture
def mock_get_current_user():
    """Fixture to mock the get_current_user dependency."""
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        odoo_url="http://fake-odoo.com",
        odoo_username="testuser",
        roles=[],
    )

    def _mock_get_current_user():
        return mock_user

    return _mock_get_current_user


@pytest.mark.asyncio
@patch("app.bulk_sync.router.kafka_producer.send_message", new_callable=AsyncMock)
async def test_bulk_sync_success(
    mock_send_message, mock_get_current_user, async_client: AsyncClient
):
    """
    Test the /bulk-sync endpoint for successful request queuing.
    - Mocks the Kafka producer's send_message method.
    - Mocks the user authentication dependency.
    - Verifies the endpoint returns a successful response.
    - Verifies that send_message was called correctly.
    """
    # Arrange
    # Override the dependency in the app
    from app.api.v1 import get_current_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Sample request payload
    sync_request_payload = {
        "inventory": [{"product_id": 101, "location_id": 202, "quantity": 50.0}],
        "purchase_orders": [],
        "sale_orders": [],
        "deliveries": [],
        "accounting_moves": [],
    }

    # Act
    response = await async_client.post("/api/v1/bulk-sync", json=sync_request_payload)

    # Assert
    # 1. Check the HTTP response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["message"] == "Bulk sync request queued for processing"

    # 2. Check if the Kafka producer's method was called
    mock_send_message.assert_awaited_once()

    # 3. Check the arguments passed to send_message
    args, kwargs = mock_send_message.call_args
    assert args[0] == "odoo-bulk-sync"  # topic
    assert args[1]["user_id"] == 1  # message payload user_id
    assert args[1]["data"] == sync_request_payload  # message payload data

    # Clean up the dependency override
    app.dependency_overrides = {}

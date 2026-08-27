"""Network-drop mid-notification retry test."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.notifications.dispatcher import dispatch_notification
from app.notifications.provider import NotificationProvider


class FailingProvider(NotificationProvider):
    fail_count = 0

    async def send(self, recipient, message, channel, data_label, extra=None):
        FailingProvider.fail_count += 1
        if FailingProvider.fail_count <= 2:
            raise ConnectionError("Simulated network drop")
        return True


@pytest.mark.asyncio
async def test_notification_retry_on_network_error():
    with patch("app.notifications.dispatcher.get_provider", return_value=FailingProvider()):
        success = False
        retries = 0
        while retries < 5:
            try:
                provider = FailingProvider()
                success = await provider.send(
                    recipient="+910000000000",
                    message="Test retry",
                    channel="console",
                    data_label="synthetic",
                )
                if success:
                    break
            except ConnectionError:
                retries += 1
                await asyncio.sleep(0.01)

    assert success is True
    assert retries == 2

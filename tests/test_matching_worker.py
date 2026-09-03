"""
Tests for matching worker Redis reconnection, retry, and graceful shutdown.
"""
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
import pytest

from app.background.matching_worker import process_matching_queue


@pytest.mark.asyncio
async def test_matching_worker_redis_retry():
    """
    Verifies that process_matching_queue does NOT terminate permanently if Redis
    is temporarily unavailable. It retries with backoff and resumes processing
    once Redis becomes available.
    """
    mock_redis = MagicMock()
    # First call to brpop returns a job, second call raises CancelledError to cleanly terminate test
    mock_redis.brpop = AsyncMock(
        side_effect=[
            ("matching_queue", json.dumps({"incident_id": "INC-TEST-RETRY"}).encode()),
            asyncio.CancelledError(),
        ]
    )

    # get_redis returns None twice, then returns mock_redis
    get_redis_mock = AsyncMock(side_effect=[None, None, mock_redis])

    with patch("app.background.matching_worker.get_redis", get_redis_mock):
        with patch("app.background.matching_worker.process_incident_match", new_callable=AsyncMock) as mock_match:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await process_matching_queue()

                # Verify get_redis was called 3 times (retried twice)
                assert get_redis_mock.call_count >= 3

                # Verify backoff sleep was invoked (1s, 2s)
                assert mock_sleep.call_count >= 2
                sleep_args = [call[0][0] for call in mock_sleep.call_args_list[:2]]
                assert sleep_args == [1, 2]

                # Verify that after connecting, the job was processed
                mock_match.assert_called_once_with("INC-TEST-RETRY")


@pytest.mark.asyncio
async def test_matching_worker_graceful_shutdown():
    """
    Verifies that when task is cancelled during sleep or brpop,
    it catches CancelledError and exits cleanly without hanging.
    """
    mock_redis = MagicMock()
    mock_redis.brpop = AsyncMock(side_effect=asyncio.CancelledError())

    with patch("app.background.matching_worker.get_redis", AsyncMock(return_value=mock_redis)):
        # Calling process_matching_queue should exit cleanly on CancelledError
        await process_matching_queue()

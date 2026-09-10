from datetime import datetime, timezone

import pytest

from quotex_ai.live_control import LiveTradingController


def test_starts_disabled() -> None:
    assert LiveTradingController().status().enabled is False


def test_auto_expires() -> None:
    controller = LiveTradingController()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    status = controller.enable(5, now)
    assert status.enabled is True
    assert controller.status(now.replace(minute=6)).enabled is False


def test_duration_is_bounded() -> None:
    with pytest.raises(ValueError):
        LiveTradingController().enable(0)

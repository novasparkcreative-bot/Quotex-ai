from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class LiveTradingStatus:
    enabled: bool
    expires_at: datetime | None = None


class LiveTradingController:
    """Fail-closed in-memory live-trading gate.

    The service always starts disabled and never persists an enabled state.
    This project does not execute real-money orders; this gate is an explicit
    safety boundary for any future broker integration.
    """

    def __init__(self) -> None:
        self._status = LiveTradingStatus(enabled=False)

    def status(self, now: datetime | None = None) -> LiveTradingStatus:
        now = now or datetime.now(timezone.utc)
        if self._status.enabled and self._status.expires_at and now >= self._status.expires_at:
            self.disable()
        return self._status

    def enable(self, duration_minutes: int, now: datetime | None = None) -> LiveTradingStatus:
        if not 1 <= duration_minutes <= 240:
            raise ValueError("duration_minutes must be between 1 and 240")
        now = now or datetime.now(timezone.utc)
        self._status = LiveTradingStatus(True, now + timedelta(minutes=duration_minutes))
        return self._status

    def disable(self) -> LiveTradingStatus:
        self._status = LiveTradingStatus(False, None)
        return self._status

    def assert_live_allowed(self, now: datetime | None = None) -> None:
        if not self.status(now).enabled:
            raise PermissionError("Live trading is disabled")

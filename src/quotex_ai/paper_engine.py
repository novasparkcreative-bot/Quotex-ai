from __future__ import annotations

import asyncio
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class PaperTrade:
    id: str
    symbol: str
    direction: str
    amount: float
    duration_seconds: int
    opened_at: str
    closed_at: str | None
    entry_price: float
    exit_price: float | None
    result: str
    pnl: float
    confidence: float


class AutonomousPaperEngine:
    """Self-running simulator. It never calls a broker order API."""

    def __init__(self) -> None:
        self.running = False
        self.interval_seconds = 30
        self.amount = 10.0
        self.duration_seconds = 60
        self._task: asyncio.Task[None] | None = None
        self._history: list[PaperTrade] = []
        self._counter = 0
        self._lock = asyncio.Lock()

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "amount": self.amount,
            "duration_seconds": self.duration_seconds,
            "interval_seconds": self.interval_seconds,
            "history_count": len(self._history),
        }

    async def start(self, amount: float = 10.0, duration_seconds: int = 60, interval_seconds: int = 30) -> dict[str, Any]:
        if not 1 <= amount <= 10000:
            raise ValueError("Paper amount must be between 1 and 10000.")
        if not 5 <= duration_seconds <= 3600:
            raise ValueError("Paper duration must be between 5 and 3600 seconds.")
        if not 5 <= interval_seconds <= 3600:
            raise ValueError("Paper interval must be between 5 and 3600 seconds.")
        self.amount = amount
        self.duration_seconds = duration_seconds
        self.interval_seconds = interval_seconds
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._loop())
        return self.status()

    async def stop(self) -> dict[str, Any]:
        self.running = False
        task = self._task
        self._task = None
        if task and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self.status()

    async def _loop(self) -> None:
        try:
            while self.running:
                # A deterministic market list keeps the simulator useful without
                # pretending that a broker quote is being received.
                symbol = random.choice(["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "XAUUSD"])
                direction = random.choice(["CALL", "PUT"])
                confidence = round(random.uniform(0.62, 0.94), 3)
                await self.open_trade(symbol, direction, confidence)
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            raise

    async def open_trade(self, symbol: str, direction: str, confidence: float) -> PaperTrade:
        self._counter += 1
        now = datetime.now(timezone.utc).isoformat()
        entry = round(100 + random.uniform(-2, 2), 5)
        # Simulation only: settle immediately with a synthetic movement.
        move = random.uniform(-0.8, 0.8)
        exit_price = round(entry + move, 5)
        won = (direction == "CALL" and exit_price > entry) or (direction == "PUT" and exit_price < entry)
        pnl = round(self.amount * (0.8 if won else -1.0), 2)
        trade = PaperTrade(
            id=f"paper-{int(time.time())}-{self._counter}",
            symbol=symbol,
            direction=direction,
            amount=self.amount,
            duration_seconds=self.duration_seconds,
            opened_at=now,
            closed_at=datetime.now(timezone.utc).isoformat(),
            entry_price=entry,
            exit_price=exit_price,
            result="WIN" if won else "LOSS",
            pnl=pnl,
            confidence=confidence,
        )
        async with self._lock:
            self._history.insert(0, trade)
            del self._history[100:]
        return trade

    def history(self) -> list[dict[str, Any]]:
        return [asdict(t) for t in self._history]

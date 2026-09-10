from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AISignal:
    symbol: str
    direction: str
    entry_conditions: list[str]
    suggested_expiry: str
    confidence: int
    invalidation: str
    generated_at: str
    paper_only: bool = True


def build_signal(symbol: str, *, price: float, previous_price: float) -> AISignal:
    """Build a transparent demo signal from supplied price data.

    This is an educational/paper signal, not a guarantee or financial advice.
    """
    if price > previous_price:
        direction = "CALL"
        conditions = ["Current price above previous observation", "Short-term momentum positive"]
        invalidation = "Do not use if price falls back below the previous observation."
    elif price < previous_price:
        direction = "PUT"
        conditions = ["Current price below previous observation", "Short-term momentum negative"]
        invalidation = "Do not use if price rises back above the previous observation."
    else:
        direction = "WAIT"
        conditions = ["No directional movement detected"]
        invalidation = "Wait for a confirmed directional move."

    confidence = 55 if direction != "WAIT" else 0
    return AISignal(
        symbol=symbol,
        direction=direction,
        entry_conditions=conditions,
        suggested_expiry="1–5 min (paper test only)" if direction != "WAIT" else "—",
        confidence=confidence,
        invalidation=invalidation,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

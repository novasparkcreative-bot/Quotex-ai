from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .live_control import LiveTradingController
from .market_data import QuotexMarketProvider, market_times

app = FastAPI(title="Quotex AI", version="0.2.0")
live_controller = LiveTradingController()
market_provider = QuotexMarketProvider()
DASHBOARD = Path(__file__).resolve().parents[2] / "static" / "dashboard.html"


class LiveEnableRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=240)


@app.get("/", include_in_schema=False)
def root():
    if DASHBOARD.exists():
        return FileResponse(DASHBOARD)
    return {"service": "quotex-ai", "status": "ok", "trading_mode": "paper"}


@app.get("/api", include_in_schema=False)
def api_root() -> dict:
    return {"service": "quotex-ai", "status": "ok", "trading_mode": "paper"}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/api/time")
def api_time() -> dict:
    return market_times()


@app.get("/api/markets")
async def markets(
    search: str = Query(default="", max_length=50),
    market: str = Query(default="all", pattern="^(all|live|otc)$"),
    asset_type: str = Query(default="all", max_length=30),
    refresh: bool = False,
) -> dict:
    items, source = await market_provider.get_markets(force_refresh=refresh)
    search_lower = search.strip().lower()
    type_lower = asset_type.strip().lower()
    filtered = []
    for item in items:
        if market == "live" and item.is_otc:
            continue
        if market == "otc" and not item.is_otc:
            continue
        if type_lower != "all" and item.market_type.lower() != type_lower:
            continue
        if search_lower and search_lower not in item.symbol.lower() and search_lower not in item.name.lower():
            continue
        filtered.append(
            {
                "symbol": item.symbol,
                "name": item.name,
                "type": item.market_type,
                "is_otc": item.is_otc,
                "is_open": item.is_open,
                "payout": item.payout,
            }
        )
    return {
        "source": source,
        "demo_only": True,
        "count": len(filtered),
        "markets": filtered,
        **market_times(),
    }


@app.get("/api/live/status")
def live_status() -> dict:
    status = live_controller.status()
    return {"enabled": status.enabled, "expires_at": status.expires_at}


@app.post("/api/live/enable")
def enable_live(request: LiveEnableRequest) -> dict:
    # This endpoint only controls the safety gate. No real-money order
    # execution is implemented or enabled by this service.
    status = live_controller.enable(request.duration_minutes)
    return {"enabled": status.enabled, "expires_at": status.expires_at}


@app.post("/api/live/disable")
def disable_live() -> dict:
    status = live_controller.disable()
    return {"enabled": status.enabled, "expires_at": status.expires_at}


@app.post("/api/live/execute")
def execute_live() -> dict:
    try:
        live_controller.assert_live_allowed()
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    raise HTTPException(
        status_code=501,
        detail="Real-money broker execution is not implemented in this build.",
    )

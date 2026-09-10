from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .live_control import LiveTradingController

app = FastAPI(title="Quotex AI", version="0.1.0")
live_controller = LiveTradingController()
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

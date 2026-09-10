# Quotex AI

Standalone FastAPI service for AI trading research and paper/demo workflows.

## Current status
- FastAPI API is available.
- Paper mode is the default.
- Timed live-trading gate is fail-closed and resets OFF on restart.
- Real-money broker execution is intentionally NOT implemented in this build.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.quotex_ai.main:app --reload --host 127.0.0.1 --port 8000
```

Open `/` or `/health` to verify the service.

## Safety
Never store credentials in Git. Keep `REAL_MONEY_ENABLED=false` unless a future broker integration has been independently verified and explicitly reviewed.

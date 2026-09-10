# Local API test runner

With the FastAPI service running locally on `127.0.0.1:8000`, run:

```bash
python scripts/test_local_api.py
```

For another local port:

```bash
python scripts/test_local_api.py --base-url http://127.0.0.1:9000
```

The runner is intentionally read-only. It checks `/health` and `/api/live/status` only. It does not enable live trading, disable live trading, or execute orders.

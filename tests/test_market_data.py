from quotex_ai.market_data import QuotexMarketProvider, market_times


def test_market_times_has_server_and_ist():
    times = market_times()
    assert times["server_timezone"] == "UTC"
    assert times["ist_timezone"] == "Asia/Kolkata"
    assert times["server_time"]
    assert times["ist_time"]


async def test_market_provider_is_unconfigured_without_credentials(monkeypatch):
    monkeypatch.delenv("QUOTEX_SSID", raising=False)
    monkeypatch.delenv("QUOTEX_EMAIL", raising=False)
    monkeypatch.delenv("QUOTEX_PASSWORD", raising=False)
    markets, source = await QuotexMarketProvider().get_markets()
    assert markets == []
    assert source == "unconfigured"

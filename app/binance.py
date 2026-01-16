import os
import aiohttp
import pandas as pd

BINANCE_BASE = os.getenv("BINANCE_BASE", "https://api.binance.com")

timeout = aiohttp.ClientTimeout(total=20)

async def get_top_usdt_symbols(n: int) -> list[str]:
    url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            r.raise_for_status()
            items = await r.json()

    usdt = [
        x for x in items
        if x.get("symbol","").endswith("USDT")
        and not x.get("symbol","").endswith("UPUSDT")
        and not x.get("symbol","").endswith("DOWNUSDT")
    ]
    usdt.sort(key=lambda x: float(x.get("quoteVolume", 0) or 0), reverse=True)
    return [x["symbol"] for x in usdt[:n]]

async def fetch_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url, params=params) as r:
            r.raise_for_status()
            data = await r.json()

    cols = [
        "open_time","open","high","low","close","volume",
        "close_time","qav","trades","tbb","tbq","ignore"
    ]
    df = pd.DataFrame(data, columns=cols)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    for c in ["open","high","low","close"]:
        df[c] = df[c].astype(float)
    return df[["open","high","low","close","close_time"]]

import os, asyncio
from app.binance import get_top_usdt_symbols, fetch_klines
from app.strategy_ualgo import compute_signal
from app.telegram import send_telegram
from app.state import load_state, save_state

TIMEFRAME = os.getenv("TIMEFRAME", "15m")
LIMIT = int(os.getenv("LIMIT", "250"))
SCAN_EVERY_SECONDS = int(os.getenv("SCAN_EVERY_SECONDS", "60"))

SYMBOLS = os.getenv("SYMBOLS", "TOP:200")  # أو: BTCUSDT,ETHUSDT,...
MULTIPLIER = float(os.getenv("MULTIPLIER", "2"))
ATR_PERIODS = int(os.getenv("ATR_PERIODS", "14"))
ATR_METHOD = os.getenv("ATR_METHOD", "Method 1")
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "2.0"))

MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "15"))

def fmt(x):
    if x is None: return "NA"
    return f"{x:.8f}".rstrip("0").rstrip(".")

async def scan_once():
    state = load_state()

    if SYMBOLS.upper().startswith("TOP:"):
        n = int(SYMBOLS.split(":",1)[1])
        symbols = await get_top_usdt_symbols(n)
    else:
        symbols = [s.strip().upper() for s in SYMBOLS.split(",") if s.strip()]

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def process(sym: str):
        async with sem:
            try:
                df = await fetch_klines(sym, TIMEFRAME, LIMIT)
                if len(df) < 50:
                    return

                res = compute_signal(
                    df,
                    multiplier=MULTIPLIER,
                    atr_periods=ATR_PERIODS,
                    atr_method=ATR_METHOD,
                    stop_loss_percent=STOP_LOSS_PERCENT
                )

                close_time = res.get("close_time")
                key = f"{sym}:{TIMEFRAME}"
                if close_time and state.get(key) == close_time:
                    return  # نفس الشمعة -> لا تكرر

                if res.get("is_long"):
                    msg = (
                        f"{sym} BUY ALERT\nTF: {TIMEFRAME}\nTime: {close_time}\n"
                        f"Entry: {fmt(res['entry'])}\n"
                        f"TP1: {fmt(res['tp_long_1'])}\nTP2: {fmt(res['tp_long_2'])}\nTP3: {fmt(res['tp_long_3'])}\n"
                        f"SL:  {fmt(res['sl_long'])}"
                    )
                    await send_telegram(msg)

                elif res.get("is_short"):
                    msg = (
                        f"{sym} SELL ALERT\nTF: {TIMEFRAME}\nTime: {close_time}\n"
                        f"Entry: {fmt(res['entry'])}\n"
                        f"TP1: {fmt(res['tp_short_1'])}\nTP2: {fmt(res['tp_short_2'])}\nTP3: {fmt(res['tp_short_3'])}\n"
                        f"SL:  {fmt(res['sl_short'])}"
                    )
                    await send_telegram(msg)

                # حتى لو ما فيه إشارة، حدّث آخر close_time لمنع إعادة الفحص لنفس الشمعة
                if close_time:
                    state[key] = close_time

            except Exception as e:
                print(f"[{sym}] error: {e}")

    await asyncio.gather(*(process(s) for s in symbols))
    save_state(state)
    print("scan done")

async def main():
    while True:
        await scan_once()
        await asyncio.sleep(SCAN_EVERY_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())

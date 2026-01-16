import numpy as np
import pandas as pd

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev = close.shift(1)
    return pd.concat([(high-low), (high-prev).abs(), (low-prev).abs()], axis=1).max(axis=1)

def atr_wilder(high, low, close, length: int):
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1/length, adjust=False).mean()

def atr_sma_tr(high, low, close, length: int):
    tr = true_range(high, low, close)
    return tr.rolling(length).mean()

def compute_signal(df: pd.DataFrame, multiplier=2.0, atr_periods=14, atr_method="Method 1", stop_loss_percent=2.0):
    o,h,l,c = df["open"], df["high"], df["low"], df["close"]
    hl2 = (h+l)/2.0
    src = hl2  # مثل سكربتك

    atr = atr_wilder(h,l,c,atr_periods) if atr_method=="Method 1" else atr_sma_tr(h,l,c,atr_periods)

    up = src - (multiplier*atr)
    dn = src + (multiplier*atr)
    up1 = up.shift(1)
    dn1 = dn.shift(1)

    trend = np.ones(len(df), dtype=int)
    for i in range(1, len(df)):
        prev = trend[i-1]
        if prev == -1 and c.iloc[i] > dn1.iloc[i]:
            trend[i] = 1
        elif prev == 1 and c.iloc[i] < up1.iloc[i]:
            trend[i] = -1
        else:
            trend[i] = prev

    trend_s = pd.Series(trend, index=df.index)
    buy = (trend_s == 1) & (trend_s.shift(1) == -1)
    sell = (trend_s == -1) & (trend_s.shift(1) == 1)

    last = df.index[-1]
    is_long = bool(buy.loc[last])
    is_short = bool(sell.loc[last])

    entry = float(c.loc[last])
    slp = (stop_loss_percent/100.0) if stop_loss_percent>0 else None

    if slp is None:
        return {"is_long": is_long, "is_short": is_short, "entry": entry}

    out = {
        "is_long": is_long,
        "is_short": is_short,
        "entry": entry,
        "sl_long": entry*(1-slp),
        "sl_short": entry*(1+slp),
        "tp_long_1": entry*(1+slp),
        "tp_long_2": entry*(1+2*slp),
        "tp_long_3": entry*(1+3*slp),
        "tp_short_1": entry*(1-slp),
        "tp_short_2": entry*(1-2*slp),
        "tp_short_3": entry*(1-3*slp),
        "trend": int(trend_s.loc[last]),
        "close_time": str(df["close_time"].iloc[-1]),
    }
    return out

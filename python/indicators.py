import pandas as pd
import numpy as np

# -------------------------
# RSI (Wilder)
# -------------------------
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0)

# -------------------------
# KD (Stochastic)
# -------------------------
def calculate_kd(df: pd.DataFrame, k_period: int = 9, d_period: int = 3):
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()

    denom = (high_max - low_min).replace(0, np.nan)
    k = ((df["Close"] - low_min) / denom) * 100
    d = k.rolling(window=d_period).mean()
    return k.fillna(0), d.fillna(0)

# -------------------------
# CCI
# -------------------------
def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
    sma = tp.rolling(period).mean()

    # Mean Deviation
    md = (tp - sma).abs().rolling(period).mean()
    cci = (tp - sma) / (0.015 * md.replace(0, np.nan))
    return cci.fillna(0)

# -------------------------
# ATR (Wilder)
# -------------------------
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            (df["High"] - df["Low"]).abs(),
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return atr.fillna(0)

# -------------------------
# Bollinger Bands
# -------------------------
def calculate_bollinger(series: pd.Series, period: int = 20, std_mult: float = 2.0):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    width = (upper - lower) / mid.replace(0, np.nan)  # 可用來看波動
    return mid.fillna(0), upper.fillna(0), lower.fillna(0), width.fillna(0)

# -------------------------
# MACD
# -------------------------
def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - macd_signal
    return macd.fillna(0), macd_signal.fillna(0), hist.fillna(0)

# -------------------------
# 支撐 / 壓力：用 Pivot High/Low 找最近的幾個水平價位（簡易版）
# -------------------------
def _pivot_levels(df: pd.DataFrame, left: int = 3, right: int = 3):
    """
    找 pivot highs/lows：某根K線的 high/low 同時大於/小於左右鄰近區間
    回傳兩個 list：pivot highs (prices), pivot lows (prices)
    """
    highs = df["High"].values
    lows = df["Low"].values

    pivot_highs = []
    pivot_lows = []

    n = len(df)
    for i in range(left, n - right):
        h = highs[i]
        l = lows[i]

        if h == np.max(highs[i-left : i+right+1]):
            pivot_highs.append(h)

        if l == np.min(lows[i-left : i+right+1]):
            pivot_lows.append(l)

    return pivot_highs, pivot_lows

def _nearest_levels(price: float, levels: list[float], top_n: int = 3):
    """
    取離目前 price 最近的幾個 level（簡單距離排序）
    """
    if not levels:
        return []
    levels = list(set([float(x) for x in levels if np.isfinite(x)]))
    levels.sort(key=lambda x: abs(x - price))
    return levels[:top_n]

# -------------------------
# 主入口：一次加完你要的所有指標
# -------------------------
def add_indicators_v2(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 型別防呆
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # === 趨勢：MA / EMA ===
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()

    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()

    # === 趨勢：MACD ===
    df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = calculate_macd(df["Close"])

    # === 超買超賣：RSI / KD / CCI ===
    df["RSI"] = calculate_rsi(df["Close"], period=14)
    df["K"], df["D"] = calculate_kd(df, k_period=9, d_period=3)
    df["CCI"] = calculate_cci(df, period=20)

    # === 波動風險：ATR / Bollinger ===
    df["ATR14"] = calculate_atr(df, period=14)
    df["BB_MID"], df["BB_UPPER"], df["BB_LOWER"], df["BB_WIDTH"] = calculate_bollinger(df["Close"], period=20, std_mult=2)

    # === 支撐壓力：成交量 & 簡易支撐壓力水平 ===
    df["VOL_MA5"] = df["Volume"].rolling(5).mean()
    df["VOL_MA20"] = df["Volume"].rolling(20).mean()

    # 用最近一段K線去找 pivot 水平（抓多了會很亂，所以取最後 120 根）
    lookback = 120
    df_recent = df.tail(lookback)

    pivot_highs, pivot_lows = _pivot_levels(df_recent, left=3, right=3)
    last_close = float(df["Close"].iloc[-1]) if len(df) else 0.0

    resistances = _nearest_levels(last_close, pivot_highs, top_n=3)
    supports = _nearest_levels(last_close, pivot_lows, top_n=3)

    # 塞進欄位（每一列都相同，方便前端直接顯示）
    df["RESIST_1"] = resistances[0] if len(resistances) > 0 else 0
    df["RESIST_2"] = resistances[1] if len(resistances) > 1 else 0
    df["RESIST_3"] = resistances[2] if len(resistances) > 2 else 0

    df["SUPPORT_1"] = supports[0] if len(supports) > 0 else 0
    df["SUPPORT_2"] = supports[1] if len(supports) > 1 else 0
    df["SUPPORT_3"] = supports[2] if len(supports) > 2 else 0

    # 最後補空值（前面 rolling 會產生 NaN）
    df.fillna(0, inplace=True)
    return df

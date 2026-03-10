from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shioaji_bridge import bridge
from indicators import add_indicators_v2, pct_change_n
from report_generator import generate_ai_markdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print("正在啟動 Shioaji Bridge...")
    bridge.login()

    yield

    # shutdown
    try:
        bridge.logout()
        print("Shioaji Bridge 已登出")
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)


# 允許跨域 (讓 Node.js 或瀏覽器可以呼叫)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "JS-Python-Trade-Bridge is Running!"}

@app.get("/api/kline/{symbol}")
def get_kline_data(symbol: str):
    print(f"正在抓取 {symbol} 資料...")

    try:
        df = bridge.get_kbars(symbol)
        if df is None:
            return {"error": "沒資料", "symbol": symbol}

        df_analyzed = add_indicators_v2(df)
        return df_analyzed.tail(100).to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ai-briefing/{code}")
def ai_briefing(code: str):
    df = bridge.get_kbars(code)
    if df is None:
        return {"error": "沒資料", "code": code}

    # 先把欄位統一成小寫，避免 Open/open 這種問題
    df2 = df.copy()
    df2.columns = [str(c).lower() for c in df2.columns]

    # 有些版本時間欄位叫 t
    if "ts" not in df2.columns and "t" in df2.columns:
        df2 = df2.rename(columns={"t": "ts"})

    want = ["ts", "open", "high", "low", "close", "volume"]
    cols = [c for c in want if c in df2.columns]

    # 如果 cols 還是空，就直接回傳目前 df2 的欄位讓你看
    if not cols:
        return {"error": "column_mismatch", "code": code, "columns": df2.columns.tolist(), "shape": list(df2.shape)}

    rows = df2[cols].tail(5).to_dict(orient="records")
    return {"code": code, "rows": rows}

@app.get("/api/ai-report/{code}")
def ai_report(code: str):
    df = bridge.get_kbars(code)
    if df is None:
        return {"error": "no_data", "code": code}

    df = add_indicators_v2(df)
    md = generate_ai_markdown(code, df)

    return {
        "code": code,
        "report": md
    }

@app.get("/api/ai-payload/{symbol}")
def get_ai_payload(symbol: str):
    try:
        df = bridge.get_kbars(symbol)
        if df is None or df.empty:
            return {"error": "no_data", "symbol": symbol}
        
        df = df.copy()

        if "ts" not in df.columns and "t" in df.columns:
            df = df.rename(columns={"t": "ts"})

        df = add_indicators_v2(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        def safe_ratio(a, b):
            return round(float(a) / float(b), 4) if float(b) != 0 else 0.0

        payload = {
            "symbol": symbol,
            "as_of": str(latest["ts"]),
            "latest": {
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "close": float(latest["Close"]),
                "volume": float(latest["Volume"]),
            },
            "indicators": {
                "ma5": float(latest["MA5"]),
                "ma20": float(latest["MA20"]),
                "ma60": float(latest["MA60"]),
                "ma120": float(latest["MA120"]),
                "ema12": float(latest["EMA12"]),
                "ema26": float(latest["EMA26"]),
                "rsi14": float(latest["RSI"]),
                "macd": float(latest["MACD"]),
                "macd_signal": float(latest["MACD_SIGNAL"]),
                "macd_hist": float(latest["MACD_HIST"]),
                "k": float(latest["K"]),
                "d": float(latest["D"]),
                "cci20": float(latest["CCI"]),
                "atr14": float(latest["ATR14"]),
                "bb_mid": float(latest["BB_MID"]),
                "bb_upper": float(latest["BB_UPPER"]),
                "bb_lower": float(latest["BB_LOWER"]),
                "bb_width": float(latest["BB_WIDTH"]),
            },
            "volume_context": {
                "volume_today": float(latest["Volume"]),
                "volume_prev_day": float(prev["Volume"]),
                "volume_ma5": float(latest["VOL_MA5"]),
                "volume_ma20": float(latest["VOL_MA20"]),
                "volume_vs_prev_day": safe_ratio(latest["Volume"], prev["Volume"]),
                "volume_vs_ma5": safe_ratio(latest["Volume"], latest["VOL_MA5"]),
                "volume_vs_ma20": safe_ratio(latest["Volume"], latest["VOL_MA20"]),
            },
            "levels": {
                "support_1": float(latest["SUPPORT_1"]),
                "support_2": float(latest["SUPPORT_2"]),
                "support_3": float(latest["SUPPORT_3"]),
                "resist_1": float(latest["RESIST_1"]),
                "resist_2": float(latest["RESIST_2"]),
                "resist_3": float(latest["RESIST_3"]),
            },
            "changes": {
                "change_1d": round(float(latest["Close"] - prev["Close"]), 2),
                "change_1d_pct": round(((float(latest["Close"]) - float(prev["Close"])) / float(prev["Close"])) * 100, 2) if float(prev["Close"]) != 0 else 0.0,
                "change_3d_pct": pct_change_n(3),
                "change_5d_pct": pct_change_n(5),
                "change_20d_pct": pct_change_n(20),
            },
            "recent_rows": df.tail(20)[["ts", "Open", "High", "Low", "Close", "Volume"]]
                .rename(columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                })
                .to_dict(orient="records"),
        }

        return payload

    except Exception as e:
        return {"error": str(e), "symbol": symbol}
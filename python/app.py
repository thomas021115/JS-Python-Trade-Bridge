from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shioaji_bridge import bridge
from indicators import add_indicators_v2
from report_generator import generate_ai_markdown

app = FastAPI()

# 允許跨域 (讓 Node.js 或瀏覽器可以呼叫)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    print("正在啟動 Shioaji Bridge...")
    bridge.login()

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
        return {"error": "欄位對不起來", "code": code, "columns": df2.columns.tolist(), "shape": list(df2.shape)}

    rows = df2[cols].tail(5).to_dict(orient="records")
    return {"code": code, "rows": rows}

@app.get("/api/ai-report/{code}")
def ai_report(code: str):
    df = bridge.get_kbars(code)
    if df is None:
        return {"error": "沒資料", "code": code}

    df = add_indicators(df)
    md = generate_ai_markdown(code, df)

    return {
        "code": code,
        "report": md
    }

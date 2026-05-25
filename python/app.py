from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import SessionLocal
from db_repository import (
    get_daily_price_between,
    get_recent_daily_price,
    save_ai_report,
    save_daily_price,
    save_stock,
    save_technical_snapshot,
)
from indicators import add_indicators_v2, pct_change_n
from report_generator import generate_ai_markdown
from shioaji_bridge import bridge


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Shioaji Bridge...")
    bridge.login()

    yield

    try:
        bridge.logout()
        print("Shioaji Bridge stopped.")
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_ratio(a, b):
    return round(float(a) / float(b), 4) if float(b) != 0 else 0.0


def _recent_rows(df, rows: int = 20):
    return (
        df.tail(rows)[["ts", "Open", "High", "Low", "Close", "Volume"]]
        .rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        .assign(ts=lambda data: data["ts"].astype(str))
        .to_dict(orient="records")
    )


def _get_db_debug_snapshot(db, symbol: str):
    target = symbol.strip()

    db_info = db.execute(text("""
        SELECT
            DATABASE() AS database_name,
            @@hostname AS mysql_hostname,
            @@port AS mysql_port,
            NOW() AS mysql_now
    """)).mappings().one()

    daily_summary = db.execute(text("""
        SELECT
            COUNT(*) AS row_count,
            MIN(ts) AS first_ts,
            MAX(ts) AS latest_ts,
            MAX(created_at) AS latest_created_at
        FROM daily_price
        WHERE symbol = :symbol
    """), {"symbol": target}).mappings().one()

    recent_daily = db.execute(text("""
        SELECT
            symbol,
            ts,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            created_at
        FROM daily_price
        WHERE symbol = :symbol
        ORDER BY ts DESC
        LIMIT 5
    """), {"symbol": target}).mappings().all()

    recent_reports = db.execute(text("""
        SELECT
            id,
            symbol,
            report_type,
            source,
            CHAR_LENGTH(report_markdown) AS report_length,
            created_at
        FROM ai_report
        WHERE symbol = :symbol
        ORDER BY id DESC
        LIMIT 5
    """), {"symbol": target}).mappings().all()

    return {
        "symbol": target,
        "database": {
            "name": db_info["database_name"],
            "mysql_hostname": db_info["mysql_hostname"],
            "mysql_port": db_info["mysql_port"],
            "mysql_now": str(db_info["mysql_now"]),
        },
        "daily_price": {
            "row_count": int(daily_summary["row_count"] or 0),
            "first_ts": str(daily_summary["first_ts"]) if daily_summary["first_ts"] else None,
            "latest_ts": str(daily_summary["latest_ts"]) if daily_summary["latest_ts"] else None,
            "latest_created_at": str(daily_summary["latest_created_at"]) if daily_summary["latest_created_at"] else None,
            "recent_rows": [dict(row) for row in recent_daily],
        },
        "ai_report": {
            "recent_rows": [dict(row) for row in recent_reports],
        },
    }


@app.get("/")
def read_root():
    return {"status": "ok", "message": "JS-Python-Trade-Bridge is Running!"}


@app.get("/api/account/stock-positions")
def get_account_stock_positions():
    try:
        rows = bridge.get_stock_positions()

        return {
            "success": True,
            "source": "shioaji",
            "count": len(rows),
            "symbols": [row["code"] for row in rows],
            "positions": rows,
        }

    except Exception as e:
        return {
            "success": False,
            "source": "shioaji",
            "error": str(e),
        }


@app.get("/api/kline/{symbol}")
def get_kline_data(symbol: str):
    print(f"Fetching kline data for {symbol}...")

    try:
        df = bridge.get_kbars(symbol)
        if df is None or df.empty:
            return {"error": "no_data", "symbol": symbol}

        df_analyzed = add_indicators_v2(df)
        return df_analyzed.tail(100).to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ai-briefing/{code}")
def ai_briefing(code: str):
    df = bridge.get_kbars(code)
    if df is None or df.empty:
        return {"error": "no_data", "code": code}

    df2 = df.copy()
    df2.columns = [str(c).lower() for c in df2.columns]

    if "ts" not in df2.columns and "t" in df2.columns:
        df2 = df2.rename(columns={"t": "ts"})

    want = ["ts", "open", "high", "low", "close", "volume"]
    cols = [c for c in want if c in df2.columns]

    if not cols:
        return {
            "error": "column_mismatch",
            "code": code,
            "columns": df2.columns.tolist(),
            "shape": list(df2.shape),
        }

    rows = df2[cols].tail(5).to_dict(orient="records")
    return {"code": code, "rows": rows}


@app.get("/api/ai-report/{code}")
def ai_report(code: str):
    code = code.strip()
    db = SessionLocal()

    try:
        df = bridge.get_kbars(code)

        if df is None or df.empty:
            return {"error": "no_data", "code": code}

        df = add_indicators_v2(df)
        md = generate_ai_markdown(code, df)

        save_stock(db, symbol=code)
        daily_count = save_daily_price(db, code, df)
        snapshot_count = save_technical_snapshot(db, code, df)
        report_id = save_ai_report(db, code, md)

        db.commit()
        db_snapshot = _get_db_debug_snapshot(db, code)

        return {
            "code": code,
            "report": md,
            "saved": True,
            "report_id": report_id,
            "daily_price_saved": daily_count,
            "technical_snapshot_saved": snapshot_count,
            "source": "shioaji",
            "db": db_snapshot,
        }

    except Exception as e:
        db.rollback()
        print("AI report error:", e)

        return {
            "code": code,
            "error": str(e),
            "saved": False,
        }

    finally:
        db.close()


@app.get("/api/debug/db/{symbol}")
def debug_database(symbol: str):
    db = SessionLocal()

    try:
        return {
            "success": True,
            **_get_db_debug_snapshot(db, symbol),
        }
    except Exception as e:
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e),
        }
    finally:
        db.close()


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
                "volume_prev_bar": float(prev["Volume"]),
                "volume_ma5": float(latest["VOL_MA5"]),
                "volume_ma20": float(latest["VOL_MA20"]),
                "volume_vs_prev_bar": _safe_ratio(latest["Volume"], prev["Volume"]),
                "volume_vs_ma5": _safe_ratio(latest["Volume"], latest["VOL_MA5"]),
                "volume_vs_ma20": _safe_ratio(latest["Volume"], latest["VOL_MA20"]),
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
                "change_1bar": round(float(latest["Close"] - prev["Close"]), 2),
                "change_1bar_pct": round(
                    ((float(latest["Close"]) - float(prev["Close"])) / float(prev["Close"])) * 100,
                    2,
                )
                if float(prev["Close"]) != 0
                else 0.0,
                "change_3bar_pct": pct_change_n(df["Close"], 3),
                "change_5bar_pct": pct_change_n(df["Close"], 5),
                "change_20bar_pct": pct_change_n(df["Close"], 20),
            },
            "recent_rows": _recent_rows(df, rows=20),
        }

        return payload

    except Exception as e:
        return {"error": str(e), "symbol": symbol}


@app.post("/api/sync/{symbol}")
def sync_stock_data(symbol: str):
    symbol = symbol.strip()
    print(f"Syncing {symbol} to MySQL...")

    db = SessionLocal()

    try:
        df = bridge.get_kbars(symbol)

        if df is None or df.empty:
            return {
                "success": False,
                "symbol": symbol,
                "error": "no_data",
            }

        df_analyzed = add_indicators_v2(df)

        save_stock(db, symbol=symbol)
        daily_count = save_daily_price(db, symbol, df_analyzed)
        snapshot_count = save_technical_snapshot(db, symbol, df_analyzed)

        db.commit()

        return {
            "success": True,
            "symbol": symbol,
            "daily_price_saved": daily_count,
            "technical_snapshot_saved": snapshot_count,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "symbol": symbol,
            "error": str(e),
        }

    finally:
        db.close()


@app.get("/api/db/kline/{symbol}")
def get_kline_from_db(symbol: str, days: int = 7):
    symbol = symbol.strip()

    db = SessionLocal()

    try:
        rows = get_recent_daily_price(db, symbol, days)

        return {
            "success": True,
            "symbol": symbol,
            "source": "database",
            "days": days,
            "count": len(rows),
            "rows": rows,
        }

    except Exception as e:
        print("Failed to read kline data from database:", e)

        return {
            "success": False,
            "symbol": symbol,
            "source": "database",
            "error": str(e),
        }

    finally:
        db.close()


@app.get("/api/test/db-kline/{symbol}")
def test_db_kline(symbol: str, start: str, end: str):
    db = SessionLocal()

    try:
        rows = get_daily_price_between(db, symbol, start, end)

        return {
            "success": True,
            "symbol": symbol,
            "start": start,
            "end": end,
            "count": len(rows),
            "first_ts": str(rows[0]["ts"]) if rows else None,
            "last_ts": str(rows[-1]["ts"]) if rows else None,
        }

    finally:
        db.close()


@app.get("/api/test/kbars/{symbol}")
def test_kbars(symbol: str, start: str, end: str):
    df = bridge.get_kbars(symbol, start=start, end=end)

    if df is None or df.empty:
        return {
            "success": False,
            "symbol": symbol,
            "error": "no_data",
        }

    return {
        "success": True,
        "symbol": symbol,
        "start": start,
        "end": end,
        "count": len(df),
        "first_ts": str(df.iloc[0]["ts"]),
        "last_ts": str(df.iloc[-1]["ts"]),
    }

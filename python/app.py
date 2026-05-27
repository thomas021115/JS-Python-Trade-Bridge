from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import SessionLocal
from db_repository import (
    get_daily_price_between,
    get_daily_price_df_between,
    get_recent_daily_price,
    save_ai_report,
    save_daily_price,
    save_stock,
    save_technical_snapshot,
)
from indicators import add_indicators_v2, pct_change_n
from report_generator import generate_ai_markdown
from shioaji_bridge import bridge


DEFAULT_REPORT_DAYS = 30
MIN_COMPLETE_1M_ROWS = 240
TIMEFRAME_1M = "1m"
TIMEFRAME_1D = "1d"
TIMEFRAME_1W = "1w"


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


def _parse_report_dates(start_date: str | None, end_date: str | None):
    today = date.today()
    parsed_end = date.fromisoformat(end_date) if end_date else today
    parsed_start = date.fromisoformat(start_date) if start_date else parsed_end - timedelta(days=DEFAULT_REPORT_DAYS)

    if parsed_start > parsed_end:
        raise ValueError("start_date cannot be later than end_date")

    start_dt = datetime.combine(parsed_start, datetime.min.time())
    end_exclusive = datetime.combine(parsed_end + timedelta(days=1), datetime.min.time())
    return parsed_start, parsed_end, start_dt, end_exclusive


def _calendar_dates(start: date, end: date):
    current = start
    dates = []

    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def _weekday_dates(start: date, end: date):
    return [d for d in _calendar_dates(start, end) if d.weekday() < 5]


def _counts_by_date(df):
    if df is None or df.empty:
        return {}

    dated = df.copy()
    dated["trade_date"] = pd.to_datetime(dated["ts"]).dt.date
    return dated.groupby("trade_date").size().to_dict()


def _compact_date_ranges(dates: list[date]):
    if not dates:
        return []

    ranges = []
    range_start = dates[0]
    previous = dates[0]

    for current in dates[1:]:
        if current == previous + timedelta(days=1):
            previous = current
            continue

        ranges.append((range_start, previous))
        range_start = current
        previous = current

    ranges.append((range_start, previous))
    return ranges


def _fetch_required_weekday_ranges(db_df, start: date, end: date):
    db_counts = _counts_by_date(db_df)
    fetch_dates = [
        d
        for d in _weekday_dates(start, end)
        if db_counts.get(d, 0) < MIN_COMPLETE_1M_ROWS
    ]
    return _compact_date_ranges(fetch_dates)


def _build_data_coverage(start: date, end: date, db_df, final_df, fetched_frames):
    db_counts = _counts_by_date(db_df)
    final_counts = _counts_by_date(final_df)
    fetched_counts = {}

    for frame in fetched_frames:
        for trade_date, count in _counts_by_date(frame).items():
            fetched_counts[trade_date] = fetched_counts.get(trade_date, 0) + int(count)

    rows = []

    for current in _calendar_dates(start, end):
        is_weekday = current.weekday() < 5
        db_count = int(db_counts.get(current, 0))
        fetched_count = int(fetched_counts.get(current, 0))
        final_count = int(final_counts.get(current, 0))
        was_fetch_attempted = is_weekday and db_count < MIN_COMPLETE_1M_ROWS

        if not is_weekday:
            source = "none"
            status = "非交易日"
        elif final_count == 0 and was_fetch_attempted:
            source = "shioaji"
            status = "可能國定假日 / 休市 / Shioaji 無資料"
        elif final_count < MIN_COMPLETE_1M_ROWS:
            source = "mixed" if db_count > 0 and fetched_count > 0 else "database" if db_count > 0 else "shioaji"
            status = "可能不完整"
        elif fetched_count > 0 and db_count > 0:
            source = "mixed"
            status = "已補抓"
        elif fetched_count > 0:
            source = "shioaji"
            status = "已補抓"
        else:
            source = "database"
            status = "完整"

        rows.append({
            "date": current.isoformat(),
            "is_trading_day": is_weekday,
            "db_count": db_count,
            "fetched_count": fetched_count,
            "kbar_count": final_count,
            "source": source,
            "status": status,
            "fetch_attempted": was_fetch_attempted,
        })

    return rows


def _add_ma_columns(df):
    enriched = df.copy()

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        enriched[col] = pd.to_numeric(enriched[col], errors="coerce").fillna(0)

    enriched["MA5"] = enriched["Close"].rolling(5).mean().fillna(0)
    enriched["MA20"] = enriched["Close"].rolling(20).mean().fillna(0)
    enriched["MA60"] = enriched["Close"].rolling(60).mean().fillna(0)
    return enriched


def _aggregate_1m_to_1d(df_1m):
    if df_1m is None or df_1m.empty:
        return pd.DataFrame(columns=["ts", "Open", "High", "Low", "Close", "Volume"])

    df = df_1m.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")
    df["trade_date"] = df["ts"].dt.normalize()

    rows = []

    for trade_date, daily in df.groupby("trade_date", sort=True):
        rows.append({
            "ts": trade_date,
            "Open": float(daily.iloc[0]["Open"]),
            "High": float(daily["High"].max()),
            "Low": float(daily["Low"].min()),
            "Close": float(daily.iloc[-1]["Close"]),
            "Volume": int(daily["Volume"].sum()),
        })

    return _add_ma_columns(pd.DataFrame(rows))


def _aggregate_1d_to_1w(df_1d):
    if df_1d is None or df_1d.empty:
        return pd.DataFrame(columns=["ts", "Open", "High", "Low", "Close", "Volume"])

    df = df_1d.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")
    df["week_start"] = (df["ts"] - pd.to_timedelta(df["ts"].dt.weekday, unit="D")).dt.normalize()

    rows = []

    for week_start, weekly in df.groupby("week_start", sort=True):
        rows.append({
            "ts": week_start,
            "Open": float(weekly.iloc[0]["Open"]),
            "High": float(weekly["High"].max()),
            "Low": float(weekly["Low"].min()),
            "Close": float(weekly.iloc[-1]["Close"]),
            "Volume": int(weekly["Volume"].sum()),
        })

    return _add_ma_columns(pd.DataFrame(rows))


def _save_higher_timeframes(db, symbol: str, df_1m):
    df_1d = _aggregate_1m_to_1d(df_1m)
    df_1w = _aggregate_1d_to_1w(df_1d)

    daily_1d = save_daily_price(db, symbol, df_1d, timeframe=TIMEFRAME_1D) if not df_1d.empty else 0
    daily_1w = save_daily_price(db, symbol, df_1w, timeframe=TIMEFRAME_1W) if not df_1w.empty else 0
    snapshot_1d = save_technical_snapshot(db, symbol, df_1d, timeframe=TIMEFRAME_1D) if not df_1d.empty else 0
    snapshot_1w = save_technical_snapshot(db, symbol, df_1w, timeframe=TIMEFRAME_1W) if not df_1w.empty else 0

    return {
        "daily_price_1d_saved": daily_1d,
        "daily_price_1w_saved": daily_1w,
        "technical_snapshot_1d_saved": snapshot_1d,
        "technical_snapshot_1w_saved": snapshot_1w,
        "df_1d": df_1d,
        "df_1w": df_1w,
    }


def _recent_rows(df, rows: int = 20):
    return (
        df.tail(rows)[["ts", "Open", "High", "Low", "Close", "Volume"]]
        .rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
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
            timeframe,
            COUNT(*) AS row_count,
            MIN(ts) AS first_ts,
            MAX(ts) AS latest_ts,
            MAX(created_at) AS latest_created_at
        FROM daily_price
        WHERE symbol = :symbol
        GROUP BY timeframe
        ORDER BY timeframe
    """), {"symbol": target}).mappings().all()

    recent_daily = db.execute(text("""
        SELECT
            symbol,
            timeframe,
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
            timeframe,
            data_source,
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
            "summary_by_timeframe": [dict(row) for row in daily_summary],
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
def ai_report(code: str, start_date: str | None = None, end_date: str | None = None):
    code = code.strip()
    db = SessionLocal()

    try:
        parsed_start, parsed_end, start_dt, end_exclusive = _parse_report_dates(start_date, end_date)
        db_df = get_daily_price_df_between(db, code, start_dt, end_exclusive, timeframe=TIMEFRAME_1M)
        fetch_ranges = _fetch_required_weekday_ranges(db_df, parsed_start, parsed_end)
        fetched_frames = []

        save_stock(db, symbol=code)

        for fetch_start, fetch_end in fetch_ranges:
            fetched_df = bridge.get_kbars(
                code,
                start=fetch_start.isoformat(),
                end=fetch_end.isoformat(),
            )

            if fetched_df is None or fetched_df.empty:
                continue

            fetched_frames.append(fetched_df)
            save_daily_price(db, code, fetched_df, timeframe=TIMEFRAME_1M)

        db.commit()

        report_df = get_daily_price_df_between(db, code, start_dt, end_exclusive, timeframe=TIMEFRAME_1M)

        if report_df.empty:
            return {
                "error": "no_data",
                "code": code,
                "start_date": parsed_start.isoformat(),
                "end_date": parsed_end.isoformat(),
                "data_source": "none",
            }

        analyzed_df = add_indicators_v2(report_df)
        snapshot_1m_count = save_technical_snapshot(db, code, analyzed_df, timeframe=TIMEFRAME_1M)
        higher = _save_higher_timeframes(db, code, report_df)
        data_coverage = _build_data_coverage(parsed_start, parsed_end, db_df, report_df, fetched_frames)

        initial_db_count = len(db_df)
        fetched_count = sum(len(frame) for frame in fetched_frames)

        if fetched_count == 0:
            data_source = "database"
        elif initial_db_count == 0:
            data_source = "shioaji"
        else:
            data_source = "mixed"

        fetched_ranges = [
            {
                "start_date": fetch_start.isoformat(),
                "end_date": fetch_end.isoformat(),
            }
            for fetch_start, fetch_end in fetch_ranges
        ]

        md = generate_ai_markdown(
            code,
            analyzed_df,
            start_date=parsed_start.isoformat(),
            end_date=parsed_end.isoformat(),
            data_source=data_source,
            data_coverage=data_coverage,
            daily_ma_df=higher["df_1d"],
            weekly_ma_df=higher["df_1w"],
        )

        report_id = save_ai_report(
            db,
            code,
            md,
            source=data_source,
            start_date=parsed_start.isoformat(),
            end_date=parsed_end.isoformat(),
            timeframe=TIMEFRAME_1M,
        )

        db.commit()
        db_snapshot = _get_db_debug_snapshot(db, code)

        return {
            "code": code,
            "report": md,
            "saved": True,
            "report_id": report_id,
            "daily_price_saved": fetched_count,
            "technical_snapshot_saved": snapshot_1m_count,
            "technical_snapshot_1d_saved": higher["technical_snapshot_1d_saved"],
            "technical_snapshot_1w_saved": higher["technical_snapshot_1w_saved"],
            "daily_price_1d_saved": higher["daily_price_1d_saved"],
            "daily_price_1w_saved": higher["daily_price_1w_saved"],
            "source": data_source,
            "data_source": data_source,
            "start_date": parsed_start.isoformat(),
            "end_date": parsed_end.isoformat(),
            "timeframe": TIMEFRAME_1M,
            "db_rows_used": len(report_df),
            "shioaji_rows_fetched": fetched_count,
            "fetched_ranges": fetched_ranges,
            "data_coverage": data_coverage,
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

        return {
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
        daily_count = save_daily_price(db, symbol, df_analyzed, timeframe=TIMEFRAME_1M)
        snapshot_count = save_technical_snapshot(db, symbol, df_analyzed, timeframe=TIMEFRAME_1M)
        higher = _save_higher_timeframes(db, symbol, df)

        db.commit()

        return {
            "success": True,
            "symbol": symbol,
            "daily_price_saved": daily_count,
            "technical_snapshot_saved": snapshot_count,
            "daily_price_1d_saved": higher["daily_price_1d_saved"],
            "daily_price_1w_saved": higher["daily_price_1w_saved"],
            "technical_snapshot_1d_saved": higher["technical_snapshot_1d_saved"],
            "technical_snapshot_1w_saved": higher["technical_snapshot_1w_saved"],
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
def get_kline_from_db(symbol: str, days: int = 7, timeframe: str = TIMEFRAME_1M):
    symbol = symbol.strip()
    db = SessionLocal()

    try:
        rows = get_recent_daily_price(db, symbol, days, timeframe=timeframe)
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
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
            "timeframe": timeframe,
            "source": "database",
            "error": str(e),
        }
    finally:
        db.close()


@app.get("/api/test/db-kline/{symbol}")
def test_db_kline(symbol: str, start: str, end: str, timeframe: str = TIMEFRAME_1M):
    db = SessionLocal()

    try:
        rows = get_daily_price_between(db, symbol, start, end, timeframe=timeframe)
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
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

from contextlib import asynccontextmanager
from datetime import date, datetime, time as datetime_time, timedelta
import time

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
DAILY_MA_WARMUP_DAYS = 120
WEEKLY_MA_WARMUP_DAYS = 450
MIN_COMPLETE_1M_ROWS = 240
SYNC_MAX_DAYS = 30
MARKET_INTRADAY_CUTOFF = datetime_time(13, 35)
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
    # 把前端日期轉成 date，另外做一組給 SQL 查詢用的 datetime。
    today = date.today()
    display_end = date.fromisoformat(end_date) if end_date else today
    display_start = date.fromisoformat(start_date) if start_date else display_end - timedelta(days=DEFAULT_REPORT_DAYS)

    if display_start > display_end:
        raise ValueError("start_date cannot be later than end_date")

    display_start_dt = datetime.combine(display_start, datetime.min.time())
    display_end_exclusive = datetime.combine(display_end + timedelta(days=1), datetime.min.time())
    return display_start, display_end, display_start_dt, display_end_exclusive


def _calc_date_ranges(display_start: date, display_end: date):
    # 顯示區間照使用者選擇，指標計算區間會多往前抓 DB 裡的 warm-up 資料。
    daily_calc_start = display_end - timedelta(days=DAILY_MA_WARMUP_DAYS)
    weekly_calc_start = display_end - timedelta(days=WEEKLY_MA_WARMUP_DAYS)
    calc_start = min(daily_calc_start, weekly_calc_start)
    calc_start_dt = datetime.combine(calc_start, datetime.min.time())
    calc_end_exclusive = datetime.combine(display_end + timedelta(days=1), datetime.min.time())

    return {
        "display_start": display_start,
        "display_end": display_end,
        "daily_calc_start": daily_calc_start,
        "weekly_calc_start": weekly_calc_start,
        "calc_start": calc_start,
        "calc_end": display_end,
        "calc_start_dt": calc_start_dt,
        "calc_end_exclusive": calc_end_exclusive,
        "uses_warmup": calc_start < display_start,
    }


def _calendar_dates(start: date, end: date):
    # 產生包含頭尾的日期清單。
    current = start
    dates = []

    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def _weekday_dates(start: date, end: date):
    # 這裡先用週一到週五當交易日，國定假日後面再另外補資料源。
    return [d for d in _calendar_dates(start, end) if d.weekday() < 5]


def _is_intraday_today(target_date: date):
    # 今天 13:35 前算盤中，不用因為資料少就判定要同步。
    now = datetime.now()
    return target_date == now.date() and now.time() < MARKET_INTRADAY_CUTOFF


def _counts_by_date(df):
    # 把 K 線資料按日期分組，回傳每天有幾筆。
    if df is None or df.empty:
        return {}

    dated = df.copy()
    dated["trade_date"] = pd.to_datetime(dated["ts"]).dt.date
    return dated.groupby("trade_date").size().to_dict()


def _compact_date_ranges(dates: list[date]):
    # 把連續缺資料日期合併成區間，方便後面回傳或同步。
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
    # 檢查哪些平日資料不足。這裡只判斷，不打 Shioaji。
    db_counts = _counts_by_date(db_df)
    fetch_dates = [
        d
        for d in _weekday_dates(start, end)
        if not _is_intraday_today(d) and db_counts.get(d, 0) < MIN_COMPLETE_1M_ROWS
    ]
    return _compact_date_ranges(fetch_dates)


def _expand_date_ranges(ranges):
    # 把日期區間展開成單日清單，主要給 API 回傳 missing_dates 用。
    dates = []

    for range_start, range_end in ranges:
        current = range_start

        while current <= range_end:
            if current.weekday() < 5:
                dates.append(current)
            current += timedelta(days=1)

    return dates


def _build_data_coverage(start: date, end: date, db_df, final_df, fetched_frames, fetch_suppressed: bool = False):
    # 組出每天的資料品質表，Markdown 和 sync-status 都會用到。
    db_counts = _counts_by_date(db_df)
    final_counts = _counts_by_date(final_df)
    fetched_counts = {}

    for frame in fetched_frames:
        for trade_date, count in _counts_by_date(frame).items():
            fetched_counts[trade_date] = fetched_counts.get(trade_date, 0) + int(count)

    rows = []

    for current in _calendar_dates(start, end):
        is_weekday = current.weekday() < 5
        is_intraday = is_weekday and _is_intraday_today(current)
        db_count = int(db_counts.get(current, 0))
        fetched_count = int(fetched_counts.get(current, 0))
        final_count = int(final_counts.get(current, 0))
        is_missing_or_sparse = is_weekday and not is_intraday and db_count < MIN_COMPLETE_1M_ROWS
        was_fetch_attempted = is_missing_or_sparse and not fetch_suppressed

        if not is_weekday:
            source = "none"
            status = "非交易日"
        elif is_intraday and final_count > 0:
            source = "mixed" if db_count > 0 and fetched_count > 0 else "database" if db_count > 0 else "shioaji"
            status = "盤中資料"
        elif is_intraday and final_count == 0:
            source = "none"
            status = "盤中尚無資料"
        elif fetch_suppressed and is_missing_or_sparse:
            source = "database" if db_count > 0 else "none"
            status = "資料缺口，待 sync/backfill"
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


def _filter_df_between_dates(df, start: date, end: date):
    # 從較大的計算區間裡切出使用者真正要看的顯示區間。
    if df is None or df.empty:
        return df

    filtered = df.copy()
    filtered["ts"] = pd.to_datetime(filtered["ts"])
    mask = (filtered["ts"].dt.date >= start) & (filtered["ts"].dt.date <= end)
    return filtered.loc[mask].sort_values("ts").reset_index(drop=True)


def _filter_weekly_for_display(df_1w, display_start: date, display_end: date):
    # 週 K 用週一當 ts，只要該週有碰到顯示區間就保留。
    if df_1w is None or df_1w.empty:
        return df_1w

    filtered = df_1w.copy()
    filtered["ts"] = pd.to_datetime(filtered["ts"])
    week_start = filtered["ts"].dt.date
    week_end = (filtered["ts"] + pd.Timedelta(days=6)).dt.date
    mask = (week_start <= display_end) & (week_end >= display_start)
    return filtered.loc[mask].sort_values("ts").reset_index(drop=True)


def _add_ma_columns(df):
    # MA 不足期數時保持 NaN，讓報告可以顯示 N/A，而不是假裝是 0。
    enriched = df.copy()

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        enriched[col] = pd.to_numeric(enriched[col], errors="coerce").fillna(0)

    for period in [5, 20, 60]:
        enriched[f"MA{period}_COUNT"] = enriched["Close"].rolling(period, min_periods=1).count()
        enriched[f"MA{period}"] = enriched["Close"].rolling(period, min_periods=period).mean()

    return enriched


def _aggregate_1m_to_1d(df_1m):
    # 從 1 分 K 聚合日 K。open 用第一筆，close 用最後一筆，volume 加總。
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
    # 從日 K 聚合週 K。每週用週一當時間戳。
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


def _save_higher_timeframes(db, symbol: str, df_1m, display_start: date, display_end: date, persist: bool = True):
    # persist=True 會寫回 DB。report 只要拿來顯示時會用 persist=False。
    df_1d_calc = _aggregate_1m_to_1d(df_1m)
    df_1w_calc = _aggregate_1d_to_1w(df_1d_calc)

    daily_1d = 0
    daily_1w = 0
    snapshot_1d = 0
    snapshot_1w = 0

    if persist:
        daily_1d = save_daily_price(db, symbol, df_1d_calc, timeframe=TIMEFRAME_1D) if not df_1d_calc.empty else 0
        daily_1w = save_daily_price(db, symbol, df_1w_calc, timeframe=TIMEFRAME_1W) if not df_1w_calc.empty else 0
        snapshot_1d = save_technical_snapshot(db, symbol, df_1d_calc, timeframe=TIMEFRAME_1D) if not df_1d_calc.empty else 0
        snapshot_1w = save_technical_snapshot(db, symbol, df_1w_calc, timeframe=TIMEFRAME_1W) if not df_1w_calc.empty else 0

    df_1d_display = _filter_df_between_dates(df_1d_calc, display_start, display_end)
    df_1w_display = _filter_weekly_for_display(df_1w_calc, display_start, display_end)

    return {
        "daily_price_1d_saved": daily_1d,
        "daily_price_1w_saved": daily_1w,
        "technical_snapshot_1d_saved": snapshot_1d,
        "technical_snapshot_1w_saved": snapshot_1w,
        "df_1d": df_1d_display,
        "df_1w": df_1w_display,
        "df_1d_calc_count": len(df_1d_calc),
        "df_1w_calc_count": len(df_1w_calc),
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
    # 報告 endpoint 只讀 DB，不主動同步 Shioaji。
    code = code.strip()
    db = SessionLocal()

    try:
        display_start, display_end, _display_start_dt, _display_end_exclusive = _parse_report_dates(start_date, end_date)
        calc_ranges = _calc_date_ranges(display_start, display_end)

        db_calc_df = get_daily_price_df_between(
            db,
            code,
            calc_ranges["calc_start_dt"],
            calc_ranges["calc_end_exclusive"],
            timeframe=TIMEFRAME_1M,
        )
        display_db_df = _filter_df_between_dates(db_calc_df, display_start, display_end)

        missing_ranges = _fetch_required_weekday_ranges(display_db_df, display_start, display_end)
        missing_fetch_dates = _expand_date_ranges(missing_ranges)
        data_quality_warning = bool(missing_fetch_dates)
        warning_message = "資料不足，請先執行資料同步" if data_quality_warning else None
        fetched_frames = []

        calc_df = get_daily_price_df_between(
            db,
            code,
            calc_ranges["calc_start_dt"],
            calc_ranges["calc_end_exclusive"],
            timeframe=TIMEFRAME_1M,
        )
        display_df = _filter_df_between_dates(calc_df, display_start, display_end)
        higher = _save_higher_timeframes(db, code, calc_df, display_start, display_end, persist=False)
        data_coverage = _build_data_coverage(
            display_start,
            display_end,
            display_db_df,
            display_df,
            fetched_frames,
            fetch_suppressed=data_quality_warning,
        )

        initial_display_db_count = len(display_db_df)
        fetched_count = 0
        data_source = "database" if initial_display_db_count > 0 else "none"

        daily_warmup_sufficient = higher["df_1d_calc_count"] >= 60
        weekly_warmup_sufficient = higher["df_1w_calc_count"] >= 60
        warmup_warning = None

        if not daily_warmup_sufficient or not weekly_warmup_sufficient:
            warmup_warning = "warm-up 資料不足，請先執行 sync/backfill"

        calculation_meta = {
            "display_start": display_start.isoformat(),
            "display_end": display_end.isoformat(),
            "daily_calc_start": calc_ranges["daily_calc_start"].isoformat(),
            "daily_calc_end": display_end.isoformat(),
            "weekly_calc_start": calc_ranges["weekly_calc_start"].isoformat(),
            "weekly_calc_end": display_end.isoformat(),
            "calc_start": calc_ranges["calc_start"].isoformat(),
            "calc_end": display_end.isoformat(),
            "uses_warmup": calc_ranges["uses_warmup"],
            "one_minute_rows_for_calc": len(calc_df),
            "daily_k_count_for_ma": higher["df_1d_calc_count"],
            "weekly_k_count_for_ma": higher["df_1w_calc_count"],
            "daily_warmup_sufficient": daily_warmup_sufficient,
            "weekly_warmup_sufficient": weekly_warmup_sufficient,
            "warmup_warning": warmup_warning,
            "missing_trading_days": [d.isoformat() for d in missing_fetch_dates],
            "data_quality_warning": data_quality_warning,
            "message": warning_message,
        }

        if display_df.empty:
            md = generate_ai_markdown(
                code,
                display_df,
                start_date=display_start.isoformat(),
                end_date=display_end.isoformat(),
                data_source=data_source,
                data_coverage=data_coverage,
                daily_ma_df=higher["df_1d"],
                weekly_ma_df=higher["df_1w"],
                calculation_meta=calculation_meta,
            )
            db.commit()

            return {
                "code": code,
                "report": md,
                "error": "no_data",
                "saved": False,
                "source": data_source,
                "data_source": data_source,
                "start_date": display_start.isoformat(),
                "end_date": display_end.isoformat(),
                "timeframe": TIMEFRAME_1M,
                "db_rows_used": 0,
                "shioaji_rows_fetched": fetched_count,
                "fetched_ranges": [],
                "missing_ranges": [
                    {"start_date": item[0].isoformat(), "end_date": item[1].isoformat()}
                    for item in missing_ranges
                ],
                "data_quality_warning": data_quality_warning,
                "message": warning_message,
                "data_coverage": data_coverage,
                "calculation_meta": calculation_meta,
            }

        analyzed_display_df = add_indicators_v2(display_df)
        snapshot_1m_count = 0

        md = generate_ai_markdown(
            code,
            analyzed_display_df,
            start_date=display_start.isoformat(),
            end_date=display_end.isoformat(),
            data_source=data_source,
            data_coverage=data_coverage,
            daily_ma_df=higher["df_1d"],
            weekly_ma_df=higher["df_1w"],
            calculation_meta=calculation_meta,
        )

        report_id = save_ai_report(
            db,
            code,
            md,
            source=data_source,
            start_date=display_start.isoformat(),
            end_date=display_end.isoformat(),
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
            "start_date": display_start.isoformat(),
            "end_date": display_end.isoformat(),
            "timeframe": TIMEFRAME_1M,
            "db_rows_used": len(display_df),
            "shioaji_rows_fetched": fetched_count,
            "fetched_ranges": [],
            "missing_ranges": [
                {"start_date": item[0].isoformat(), "end_date": item[1].isoformat()}
                for item in missing_ranges
            ],
            "data_quality_warning": data_quality_warning,
            "message": warning_message,
            "data_coverage": data_coverage,
            "calculation_meta": calculation_meta,
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


@app.get("/api/sync-status/{symbol}")
def get_sync_status(symbol: str, start_date: str | None = None, end_date: str | None = None):
    # 同步前先查 DB 覆蓋率。這裡不能打 Shioaji。
    symbol = symbol.strip()
    db = SessionLocal()

    try:
        display_start, display_end, display_start_dt, display_end_exclusive = _parse_report_dates(start_date, end_date)
        db_df = get_daily_price_df_between(
            db,
            symbol,
            display_start_dt,
            display_end_exclusive,
            timeframe=TIMEFRAME_1M,
        )
        missing_ranges = _fetch_required_weekday_ranges(db_df, display_start, display_end)
        missing_dates = [d.isoformat() for d in _expand_date_ranges(missing_ranges)]
        needs_sync = bool(missing_dates)
        range_days = (display_end - display_start).days + 1
        can_sync_once = range_days <= SYNC_MAX_DAYS
        message = None

        if not can_sync_once:
            message = "同步區間超過 30 天，請縮小範圍"
        elif needs_sync:
            message = "資料不足，請先執行資料同步"
        else:
            message = "資料已完整，不需要同步"

        coverage = _build_data_coverage(
            display_start,
            display_end,
            db_df,
            db_df,
            [],
            fetch_suppressed=needs_sync,
        )

        return {
            "success": True,
            "symbol": symbol,
            "start_date": display_start.isoformat(),
            "end_date": display_end.isoformat(),
            "timeframe": TIMEFRAME_1M,
            "needs_sync": needs_sync,
            "can_sync_once": can_sync_once,
            "max_sync_days": SYNC_MAX_DAYS,
            "range_days": range_days,
            "missing_dates": missing_dates,
            "coverage": coverage,
            "message": message,
        }
    except Exception as e:
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e),
        }
    finally:
        db.close()


@app.post("/api/sync/{symbol}")
def sync_stock_data(symbol: str, start_date: str | None = None, end_date: str | None = None):
    # 同步 endpoint 才會打 Shioaji，並把 1m、1d、1w 寫回 DB。
    symbol = symbol.strip()
    print(f"Syncing {symbol} to MySQL...")

    db = SessionLocal()
    started_at = time.perf_counter()

    try:
        sync_end = date.fromisoformat(end_date) if end_date else date.today()
        sync_start = date.fromisoformat(start_date) if start_date else sync_end - timedelta(days=DEFAULT_REPORT_DAYS - 1)
        sync_days = (sync_end - sync_start).days + 1

        if sync_start > sync_end:
            return {
                "success": False,
                "symbol": symbol,
                "error": "start_date cannot be later than end_date",
                "elapsed_seconds": round(time.perf_counter() - started_at, 2),
            }

        if sync_days > SYNC_MAX_DAYS:
            return {
                "success": False,
                "symbol": symbol,
                "start_date": sync_start.isoformat(),
                "end_date": sync_end.isoformat(),
                "max_days": SYNC_MAX_DAYS,
                "requested_days": sync_days,
                "error": f"sync range too large; max {SYNC_MAX_DAYS} days",
                "message": f"單次 sync 最多允許 {SYNC_MAX_DAYS} 天，請縮小區間或分批同步",
                "elapsed_seconds": round(time.perf_counter() - started_at, 2),
            }

        df = bridge.get_kbars(
            symbol,
            start=sync_start.isoformat(),
            end=sync_end.isoformat(),
        )

        if df is None or df.empty:
            return {
                "success": False,
                "symbol": symbol,
                "start_date": sync_start.isoformat(),
                "end_date": sync_end.isoformat(),
                "error": "no_data",
                "elapsed_seconds": round(time.perf_counter() - started_at, 2),
            }

        df_analyzed = add_indicators_v2(df)

        save_stock(db, symbol=symbol)
        daily_count = save_daily_price(db, symbol, df, timeframe=TIMEFRAME_1M)
        snapshot_count = save_technical_snapshot(db, symbol, df_analyzed, timeframe=TIMEFRAME_1M)

        calc_ranges = _calc_date_ranges(sync_start, sync_end)
        calc_df = get_daily_price_df_between(
            db,
            symbol,
            calc_ranges["calc_start_dt"],
            calc_ranges["calc_end_exclusive"],
            timeframe=TIMEFRAME_1M,
        )
        higher = _save_higher_timeframes(db, symbol, calc_df, sync_start, sync_end, persist=True)

        db.commit()

        return {
            "success": True,
            "symbol": symbol,
            "start_date": sync_start.isoformat(),
            "end_date": sync_end.isoformat(),
            "timeframe": TIMEFRAME_1M,
            "fetched_rows": len(df),
            "saved_1m_rows": daily_count,
            "daily_price_saved": daily_count,
            "technical_snapshot_saved": snapshot_count,
            "saved_1d_rows": higher["daily_price_1d_saved"],
            "saved_1w_rows": higher["daily_price_1w_saved"],
            "daily_price_1d_saved": higher["daily_price_1d_saved"],
            "daily_price_1w_saved": higher["daily_price_1w_saved"],
            "technical_snapshot_1d_saved": higher["technical_snapshot_1d_saved"],
            "technical_snapshot_1w_saved": higher["technical_snapshot_1w_saved"],
            "elapsed_seconds": round(time.perf_counter() - started_at, 2),
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e),
            "elapsed_seconds": round(time.perf_counter() - started_at, 2),
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

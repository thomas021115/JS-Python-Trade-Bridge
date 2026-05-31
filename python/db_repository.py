from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text

def save_ai_report(
    db,
    symbol: str,
    report_markdown: str,
    report_type: str = "technical_mvp",
    source: str = "shioaji",
    start_date: str | None = None,
    end_date: str | None = None,
    timeframe: str = "1m",
):
    # 儲存產出的 Markdown。這張表是報告紀錄，不是 K 線原始資料。
    sql = text("""
        INSERT INTO ai_report (
            symbol,
            report_type,
            report_markdown,
            start_date,
            end_date,
            timeframe,
            data_source
        )
        VALUES (
            :symbol,
            :report_type,
            :report_markdown,
            :start_date,
            :end_date,
            :timeframe,
            :data_source
        )
    """)

    result = db.execute(sql, {
        "symbol": symbol,
        "report_type": report_type,
        "report_markdown": report_markdown,
        "start_date": start_date,
        "end_date": end_date,
        "timeframe": timeframe,
        "data_source": source,
    })

    return result.lastrowid

def save_stock(db, symbol: str, name: str | None = None, market: str | None = None):
    # 股票基本資料只保留一筆。重複 symbol 會更新名稱或市場。
    sql = text("""
        INSERT INTO stocks (symbol, name, market)
        VALUES (:symbol, :name, :market)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            market = VALUES(market)
    """)

    db.execute(sql, {
        "symbol": symbol,
        "name": name,
        "market": market
    })


def save_daily_price(db, symbol: str, df, timeframe: str = "1m"):
    # 寫入 K 線資料。唯一鍵是 symbol + timeframe + ts，所以可以安全 upsert。
    sql = text("""
        INSERT INTO daily_price (
            symbol,
            timeframe,
            ts,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        )
        VALUES (
            :symbol,
            :timeframe,
            :ts,
            :open_price,
            :high_price,
            :low_price,
            :close_price,
            :volume
        )
        ON DUPLICATE KEY UPDATE
            timeframe = VALUES(timeframe),
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            volume = VALUES(volume)
    """)

    count = 0

    for _, row in df.iterrows():
        db.execute(sql, {
            "symbol": symbol,
            "timeframe": timeframe,
            "ts": row["ts"],
            "open_price": float(row["Open"]),
            "high_price": float(row["High"]),
            "low_price": float(row["Low"]),
            "close_price": float(row["Close"]),
            "volume": int(row["Volume"]),
        })
        count += 1

    return count


def _float_value(row, key: str):
    # 技術指標可能還沒算出來，沒有值就寫 NULL。
    if key not in row:
        return None

    value = row[key]
    if pd.isna(value):
        return None

    return float(value)


def save_technical_snapshot(db, symbol: str, df, timeframe: str = "1m"):
    # 寫入技術指標快照。日 K、週 K、1 分 K 都靠 timeframe 區分。
    sql = text("""
        INSERT INTO technical_snapshot (
            symbol,
            timeframe,
            ts,
            ma5,
            ma20,
            ma60,
            ma120,
            ema12,
            ema26,
            rsi14,
            macd,
            macd_signal,
            macd_hist,
            k_value,
            d_value,
            cci20,
            atr14,
            bb_mid,
            bb_upper,
            bb_lower,
            bb_width,
            vol_ma5,
            vol_ma20,
            support_1,
            support_2,
            support_3,
            resist_1,
            resist_2,
            resist_3
        )
        VALUES (
            :symbol,
            :timeframe,
            :ts,
            :ma5,
            :ma20,
            :ma60,
            :ma120,
            :ema12,
            :ema26,
            :rsi14,
            :macd,
            :macd_signal,
            :macd_hist,
            :k_value,
            :d_value,
            :cci20,
            :atr14,
            :bb_mid,
            :bb_upper,
            :bb_lower,
            :bb_width,
            :vol_ma5,
            :vol_ma20,
            :support_1,
            :support_2,
            :support_3,
            :resist_1,
            :resist_2,
            :resist_3
        )
        ON DUPLICATE KEY UPDATE
            timeframe = VALUES(timeframe),
            ma5 = VALUES(ma5),
            ma20 = VALUES(ma20),
            ma60 = VALUES(ma60),
            ma120 = VALUES(ma120),
            ema12 = VALUES(ema12),
            ema26 = VALUES(ema26),
            rsi14 = VALUES(rsi14),
            macd = VALUES(macd),
            macd_signal = VALUES(macd_signal),
            macd_hist = VALUES(macd_hist),
            k_value = VALUES(k_value),
            d_value = VALUES(d_value),
            cci20 = VALUES(cci20),
            atr14 = VALUES(atr14),
            bb_mid = VALUES(bb_mid),
            bb_upper = VALUES(bb_upper),
            bb_lower = VALUES(bb_lower),
            bb_width = VALUES(bb_width),
            vol_ma5 = VALUES(vol_ma5),
            vol_ma20 = VALUES(vol_ma20),
            support_1 = VALUES(support_1),
            support_2 = VALUES(support_2),
            support_3 = VALUES(support_3),
            resist_1 = VALUES(resist_1),
            resist_2 = VALUES(resist_2),
            resist_3 = VALUES(resist_3)
    """)

    count = 0

    for _, row in df.iterrows():
        db.execute(sql, {
            "symbol": symbol,
            "timeframe": timeframe,
            "ts": row["ts"],
            "ma5": _float_value(row, "MA5"),
            "ma20": _float_value(row, "MA20"),
            "ma60": _float_value(row, "MA60"),
            "ma120": _float_value(row, "MA120"),
            "ema12": _float_value(row, "EMA12"),
            "ema26": _float_value(row, "EMA26"),
            "rsi14": _float_value(row, "RSI"),
            "macd": _float_value(row, "MACD"),
            "macd_signal": _float_value(row, "MACD_SIGNAL"),
            "macd_hist": _float_value(row, "MACD_HIST"),
            "k_value": _float_value(row, "K"),
            "d_value": _float_value(row, "D"),
            "cci20": _float_value(row, "CCI"),
            "atr14": _float_value(row, "ATR14"),
            "bb_mid": _float_value(row, "BB_MID"),
            "bb_upper": _float_value(row, "BB_UPPER"),
            "bb_lower": _float_value(row, "BB_LOWER"),
            "bb_width": _float_value(row, "BB_WIDTH"),
            "vol_ma5": _float_value(row, "VOL_MA5"),
            "vol_ma20": _float_value(row, "VOL_MA20"),
            "support_1": _float_value(row, "SUPPORT_1"),
            "support_2": _float_value(row, "SUPPORT_2"),
            "support_3": _float_value(row, "SUPPORT_3"),
            "resist_1": _float_value(row, "RESIST_1"),
            "resist_2": _float_value(row, "RESIST_2"),
            "resist_3": _float_value(row, "RESIST_3"),
        })
        count += 1

    return count

def get_recent_daily_price(db, symbol: str, days: int = 7, timeframe: str = "1m"):
    # 給 API 快速查最近幾天 K 線用。
    start_time = datetime.now() - timedelta(days=days)

    sql = text("""
        SELECT
            symbol,
            timeframe,
            ts,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        FROM daily_price
        WHERE symbol = :symbol
          AND timeframe = :timeframe
          AND ts >= :start_time
        ORDER BY ts ASC
    """)

    result = db.execute(sql, {
        "symbol": symbol,
        "timeframe": timeframe,
        "start_time": start_time
    })

    rows = []

    for row in result:
        data = dict(row._mapping)

        rows.append({
            "symbol": data["symbol"],
            "timeframe": data["timeframe"],
            "ts": data["ts"].isoformat(),
            "open": float(data["open_price"]),
            "high": float(data["high_price"]),
            "low": float(data["low_price"]),
            "close": float(data["close_price"]),
            "volume": int(data["volume"]),
        })

    return rows

def get_daily_price_between(db, symbol: str, start_time, end_time, timeframe: str = "1m"):
    # 查指定時間區間。end_time 用小於，避免跨日查詢重複拿到邊界資料。
    sql = text("""
        SELECT
            symbol,
            timeframe,
            ts,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        FROM daily_price
        WHERE symbol = :symbol
          AND timeframe = :timeframe
          AND ts >= :start_time
          AND ts < :end_time
        ORDER BY ts ASC
    """)

    result = db.execute(sql, {
        "symbol": symbol,
        "timeframe": timeframe,
        "start_time": start_time,
        "end_time": end_time,
    })

    rows = []

    for row in result:
        rows.append(dict(row._mapping))

    return rows


def get_daily_price_df_between(db, symbol: str, start_time, end_time, timeframe: str = "1m"):
    # app.py 大多用 DataFrame 處理指標和聚合，所以這裡直接包一層轉換。
    rows = get_daily_price_between(db, symbol, start_time, end_time, timeframe=timeframe)
    return daily_price_rows_to_df(rows)


def daily_price_rows_to_df(rows):
    # 把 DB 欄位名稱轉回 pandas 計算時使用的欄位名稱。
    if not rows:
        return pd.DataFrame(columns=["ts", "Open", "High", "Low", "Close", "Volume"])

    normalized = []

    for row in rows:
        normalized.append({
            "ts": row["ts"],
            "Open": float(row["open_price"]),
            "High": float(row["high_price"]),
            "Low": float(row["low_price"]),
            "Close": float(row["close_price"]),
            "Volume": int(row["volume"]),
        })

    df = pd.DataFrame(normalized)
    df["ts"] = pd.to_datetime(df["ts"])
    return df.sort_values("ts").reset_index(drop=True)

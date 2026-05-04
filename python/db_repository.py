from sqlalchemy import text

def save_ai_report(db, symbol: str, report_markdown: str):
    sql = text("""
        INSERT INTO ai_report (
            symbol,
            report_markdown
        )
        VALUES (
            :symbol,
            :report_markdown
        )
    """)

    db.execute(sql, {
        "symbol": symbol,
        "report_markdown": report_markdown
    })

def save_stock(db, symbol: str, name: str | None = None, market: str | None = None):
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


def save_daily_price(db, symbol: str, df):
    sql = text("""
        INSERT INTO daily_price (
            symbol,
            ts,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        )
        VALUES (
            :symbol,
            :ts,
            :open_price,
            :high_price,
            :low_price,
            :close_price,
            :volume
        )
        ON DUPLICATE KEY UPDATE
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
            "ts": row["ts"],
            "open_price": float(row["Open"]),
            "high_price": float(row["High"]),
            "low_price": float(row["Low"]),
            "close_price": float(row["Close"]),
            "volume": int(row["Volume"]),
        })
        count += 1

    return count


def save_technical_snapshot(db, symbol: str, df):
    sql = text("""
        INSERT INTO technical_snapshot (
            symbol,
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
            "ts": row["ts"],
            "ma5": float(row["MA5"]),
            "ma20": float(row["MA20"]),
            "ma60": float(row["MA60"]),
            "ma120": float(row["MA120"]),
            "ema12": float(row["EMA12"]),
            "ema26": float(row["EMA26"]),
            "rsi14": float(row["RSI"]),
            "macd": float(row["MACD"]),
            "macd_signal": float(row["MACD_SIGNAL"]),
            "macd_hist": float(row["MACD_HIST"]),
            "k_value": float(row["K"]),
            "d_value": float(row["D"]),
            "cci20": float(row["CCI"]),
            "atr14": float(row["ATR14"]),
            "bb_mid": float(row["BB_MID"]),
            "bb_upper": float(row["BB_UPPER"]),
            "bb_lower": float(row["BB_LOWER"]),
            "bb_width": float(row["BB_WIDTH"]),
            "vol_ma5": float(row["VOL_MA5"]),
            "vol_ma20": float(row["VOL_MA20"]),
            "support_1": float(row["SUPPORT_1"]),
            "support_2": float(row["SUPPORT_2"]),
            "support_3": float(row["SUPPORT_3"]),
            "resist_1": float(row["RESIST_1"]),
            "resist_2": float(row["RESIST_2"]),
            "resist_3": float(row["RESIST_3"]),
        })
        count += 1

    return count
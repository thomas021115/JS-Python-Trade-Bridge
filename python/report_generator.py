from __future__ import annotations

import math
from typing import Any

import pandas as pd


MAX_DAILY_SAMPLE_ROWS = 120


def _num(value: Any, digits: int = 2) -> float:
    try:
        numeric = float(value)
        if value is None or pd.isna(value) or not math.isfinite(numeric):
            return 0.0
        return round(numeric, digits)
    except (TypeError, ValueError):
        return 0.0


def _pct(current: Any, previous: Any) -> float:
    previous_value = _num(previous, 6)
    if previous_value == 0:
        return 0.0
    return round((_num(current, 6) - previous_value) / previous_value * 100, 2)


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["ts"] = pd.to_datetime(prepared["ts"])
    return prepared.sort_values("ts").reset_index(drop=True)


def _format_coverage_rows(data_coverage: list[dict[str, Any]] | None) -> str:
    if not data_coverage:
        return "尚無資料覆蓋狀態。"

    lines = [
        "| 日期 | 是否交易日 | K 線資料筆數 | 來源 | 狀態 | DB 原始筆數 | 本次補抓筆數 |",
        "| :--- | :---: | ---: | :--- | :--- | ---: | ---: |",
    ]

    for row in data_coverage:
        lines.append(
            "| {date} | {is_trading_day} | {kbar_count} | {source} | {status} | {db_count} | {fetched_count} |".format(
                date=row.get("date", "-"),
                is_trading_day="是" if row.get("is_trading_day") else "否",
                kbar_count=int(row.get("kbar_count") or 0),
                source=row.get("source", "-"),
                status=row.get("status", "-"),
                db_count=int(row.get("db_count") or 0),
                fetched_count=int(row.get("fetched_count") or 0),
            )
        )

    return "\n".join(lines)


def _format_bool(value: Any) -> str:
    return "是" if value else "否"


def _format_calculation_meta(meta: dict[str, Any] | None) -> str:
    if not meta:
        return "尚無指標計算資料範圍。"

    rows = [
        ("使用者顯示區間", f"{meta.get('display_start', '-')} ~ {meta.get('display_end', '-')}"),
        ("日 K MA 計算用區間", f"{meta.get('daily_calc_start', '-')} ~ {meta.get('daily_calc_end', '-')}"),
        ("週 K MA 計算用區間", f"{meta.get('weekly_calc_start', '-')} ~ {meta.get('weekly_calc_end', '-')}"),
        ("是否使用 warm-up 歷史資料", _format_bool(meta.get("uses_warmup"))),
        ("1m 計算可用筆數", meta.get("one_minute_rows_for_calc", 0)),
        ("日 K 實際使用根數", meta.get("daily_k_count_for_ma", 0)),
        ("週 K 實際使用根數", meta.get("weekly_k_count_for_ma", 0)),
        ("日 K warm-up 是否足夠", _format_bool(meta.get("daily_warmup_sufficient"))),
        ("週 K warm-up 是否足夠", _format_bool(meta.get("weekly_warmup_sufficient"))),
    ]

    if meta.get("data_quality_warning"):
        rows.append(("資料缺口警告", meta.get("message") or "資料不足，請先執行資料同步"))

    if meta.get("warmup_warning"):
        rows.append(("warm-up 警告", meta.get("warmup_warning")))

    lines = [
        "| 項目 | 值 |",
        "| :--- | :--- |",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return "\n".join(lines)


def _format_range_summary(df: pd.DataFrame) -> str:
    first = df.iloc[0]
    last = df.iloc[-1]
    close_change = _num(last.get("Close") - first.get("Open"))
    close_change_pct = _pct(last.get("Close"), first.get("Open"))
    grouped_days = df["ts"].dt.date.nunique()

    rows = [
        ("第一筆時間", first.get("ts")),
        ("最後一筆時間", last.get("ts")),
        ("涵蓋交易日數", grouped_days),
        ("1m K 線筆數", len(df)),
        ("區間開盤", _num(first.get("Open"))),
        ("區間最高", _num(df["High"].max())),
        ("區間最低", _num(df["Low"].min())),
        ("區間最後收盤", _num(last.get("Close"))),
        ("區間變化", close_change),
        ("區間變化百分比", f"{close_change_pct}%"),
        ("區間總量", int(_num(df["Volume"].sum(), 0))),
    ]

    lines = [
        "| 項目 | 值 |",
        "| :--- | :--- |",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return "\n".join(lines)


def _format_daily_ohlcv_summary(df: pd.DataFrame) -> str:
    lines = [
        "| 日期 | 第一筆時間 | 最後一筆時間 | 筆數 | 開盤 | 最高 | 最低 | 收盤 | 量 |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for trade_date, daily in df.groupby(df["ts"].dt.date, sort=True):
        first = daily.iloc[0]
        last = daily.iloc[-1]
        lines.append(
            "| {date} | {first_ts} | {last_ts} | {count} | {open} | {high} | {low} | {close} | {volume} |".format(
                date=trade_date,
                first_ts=first["ts"],
                last_ts=last["ts"],
                count=len(daily),
                open=_num(first["Open"]),
                high=_num(daily["High"].max()),
                low=_num(daily["Low"].min()),
                close=_num(last["Close"]),
                volume=int(_num(daily["Volume"].sum(), 0)),
            )
        )

    return "\n".join(lines)


def _format_indicator_snapshot(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    indicators = [
        ("Close", last.get("Close")),
        ("MA5", last.get("MA5")),
        ("MA20", last.get("MA20")),
        ("MA60", last.get("MA60")),
        ("MA120", last.get("MA120")),
        ("EMA12", last.get("EMA12")),
        ("EMA26", last.get("EMA26")),
        ("RSI14", last.get("RSI")),
        ("MACD", last.get("MACD")),
        ("MACD Signal", last.get("MACD_SIGNAL")),
        ("MACD Hist", last.get("MACD_HIST")),
        ("K", last.get("K")),
        ("D", last.get("D")),
        ("CCI20", last.get("CCI")),
        ("ATR14", last.get("ATR14")),
        ("BB Mid", last.get("BB_MID")),
        ("BB Upper", last.get("BB_UPPER")),
        ("BB Lower", last.get("BB_LOWER")),
        ("BB Width", last.get("BB_WIDTH")),
        ("VOL MA5", last.get("VOL_MA5")),
        ("VOL MA20", last.get("VOL_MA20")),
    ]

    lines = [
        "| 指標 | 最新值 |",
        "| :--- | ---: |",
    ]
    lines.extend(f"| {name} | {_num(value, 4)} |" for name, value in indicators)
    return "\n".join(lines)


def _format_ma_value(row: pd.Series, period: int) -> str:
    value = row.get(f"MA{period}")
    current_count = int(row.get(f"MA{period}_COUNT", 0) or 0)

    if value is None or pd.isna(value):
        return f"N/A（需 {period}，目前 {current_count}）"

    return str(_num(value, 4))


def _format_ma_table(df: pd.DataFrame | None, timeframe: str) -> str:
    if df is None or df.empty:
        return f"尚無 {timeframe} MA 資料。"

    prepared = _prepare_df(df)
    lines = [
        "| 日期 | 開盤 | 最高 | 最低 | 收盤 | 量 | MA5 | MA20 | MA60 |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for _, row in prepared.iterrows():
        lines.append(
            "| {ts} | {open} | {high} | {low} | {close} | {volume} | {ma5} | {ma20} | {ma60} |".format(
                ts=row["ts"],
                open=_num(row["Open"]),
                high=_num(row["High"]),
                low=_num(row["Low"]),
                close=_num(row["Close"]),
                volume=int(_num(row["Volume"], 0)),
                ma5=_format_ma_value(row, 5),
                ma20=_format_ma_value(row, 20),
                ma60=_format_ma_value(row, 60),
            )
        )

    return "\n".join(lines)


def _format_levels(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    return "\n".join([
        "| 類型 | 價位 1 | 價位 2 | 價位 3 |",
        "| :--- | ---: | ---: | ---: |",
        f"| 支撐 | {_num(last.get('SUPPORT_1'))} | {_num(last.get('SUPPORT_2'))} | {_num(last.get('SUPPORT_3'))} |",
        f"| 壓力 | {_num(last.get('RESIST_1'))} | {_num(last.get('RESIST_2'))} | {_num(last.get('RESIST_3'))} |",
    ])


def _format_one_minute_rows(df: pd.DataFrame) -> str:
    if df.empty:
        return "本區間內沒有可列出的 1 分 K 線資料。"

    sections = []

    for trade_date, daily in df.groupby(df["ts"].dt.date, sort=True):
        sample = daily.tail(MAX_DAILY_SAMPLE_ROWS)
        lines = [
            f"### {trade_date}（最後 {len(sample)} 筆）",
            "",
            "| 時間 | 開盤 | 最高 | 最低 | 收盤 | 量 |",
            "| :--- | ---: | ---: | ---: | ---: | ---: |",
        ]

        for _, row in sample.iterrows():
            lines.append(
                "| {ts} | {open} | {high} | {low} | {close} | {volume} |".format(
                    ts=row["ts"],
                    open=_num(row["Open"]),
                    high=_num(row["High"]),
                    low=_num(row["Low"]),
                    close=_num(row["Close"]),
                    volume=int(_num(row["Volume"], 0)),
                )
            )

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def generate_ai_markdown(
    symbol: str,
    df: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    data_source: str | None = None,
    data_coverage: list[dict[str, Any]] | None = None,
    daily_ma_df: pd.DataFrame | None = None,
    weekly_ma_df: pd.DataFrame | None = None,
    calculation_meta: dict[str, Any] | None = None,
) -> str:
    coverage_table = _format_coverage_rows(data_coverage)
    calculation_range = _format_calculation_meta(calculation_meta)
    date_range = f"{start_date or '-'} ~ {end_date or '-'}"
    source_label = data_source or "unknown"

    if df is None or df.empty:
        return f"""# {symbol} AI 技術分析資料包

> 分析區間：{date_range}
> 資料來源：{source_label}
> 最新資料時間：-
> 使用資料筆數：0 筆

## 1. 資料覆蓋狀態
{coverage_table}

## 2. 指標計算資料範圍
{calculation_range}

本區間內沒有可分析的 1 分 K 線資料。"""

    prepared = _prepare_df(df)
    last = prepared.iloc[-1]

    return f"""# {symbol} AI 技術分析資料包

> 分析區間：{date_range}
> 資料來源：{source_label}
> 最新資料時間：{last.get("ts", "-")}
> 使用資料筆數：{len(prepared)} 筆

## 1. 資料覆蓋狀態
{coverage_table}

## 2. 指標計算資料範圍
{calculation_range}

## 3. 區間統計摘要
{_format_range_summary(prepared)}

## 4. 每日 OHLCV 摘要
{_format_daily_ohlcv_summary(prepared)}

## 5. 1m 技術指標快照
{_format_indicator_snapshot(prepared)}

## 6. 日 K MA5 / MA20 / MA60
{_format_ma_table(daily_ma_df, "1d")}

## 7. 週 K MA5 / MA20 / MA60
{_format_ma_table(weekly_ma_df, "1w")}

## 8. 支撐壓力
{_format_levels(prepared)}

## 9. 每日 1 分 K 線樣本
{_format_one_minute_rows(prepared)}
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _num(value: Any, digits: int = 2) -> float:
    try:
        if value is None or not math.isfinite(float(value)):
            return 0.0
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


def _pct(current: Any, previous: Any) -> float:
    previous_value = _num(previous, 6)
    if previous_value == 0:
        return 0.0
    return round((_num(current, 6) - previous_value) / previous_value * 100, 2)


def _trend_label(last: pd.Series) -> str:
    close = _num(last.get("Close"))
    ma5 = _num(last.get("MA5"))
    ma20 = _num(last.get("MA20"))
    macd_hist = _num(last.get("MACD_HIST"))

    if close > ma5 > ma20 and macd_hist > 0:
        return "偏多"
    if close < ma5 < ma20 and macd_hist < 0:
        return "偏空"
    return "震盪"


def _risk_label(last: pd.Series) -> str:
    rsi = _num(last.get("RSI"))
    bb_width = _num(last.get("BB_WIDTH"), 4)

    if rsi >= 70:
        return "RSI 偏熱，追價風險較高"
    if rsi <= 30:
        return "RSI 偏低，留意反彈或弱勢延續"
    if bb_width > 0.08:
        return "波動放大，停損距離需要拉開"
    return "指標位於中性區，等待量價突破"


def _format_recent_rows(df: pd.DataFrame, rows: int = 20) -> str:
    recent = df.tail(rows)[["ts", "Open", "High", "Low", "Close", "Volume"]].copy()
    recent.columns = ["時間", "開盤", "最高", "最低", "收盤", "量"]

    lines = [
        "| 時間 | 開盤 | 最高 | 最低 | 收盤 | 量 |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for _, row in recent.iterrows():
        lines.append(
            "| {ts} | {open} | {high} | {low} | {close} | {volume} |".format(
                ts=row["時間"],
                open=_num(row["開盤"]),
                high=_num(row["最高"]),
                low=_num(row["最低"]),
                close=_num(row["收盤"]),
                volume=int(_num(row["量"], 0)),
            )
        )

    return "\n".join(lines)


def generate_ai_markdown(symbol: str, df: pd.DataFrame) -> str:
    """
    Generate a deterministic MVP markdown report from analyzed kbar data.

    This function does not call an LLM yet. It turns the fetched Shioaji data
    plus calculated indicators into a fuller report that can be saved and
    previewed immediately.
    """
    if df is None or df.empty:
        return f"# {symbol} AI 技術戰報\n\n目前沒有可分析的 K 線資料。"

    if len(df) < 2:
        last = df.iloc[-1]
        return f"# {symbol} AI 技術戰報\n\n資料筆數不足，僅取得 1 筆：{last.get('ts', '-')}"

    last = df.iloc[-1]
    prev = df.iloc[-2]
    recent = df.tail(20)

    close = _num(last.get("Close"))
    prev_close = _num(prev.get("Close"))
    change = round(close - prev_close, 2)
    change_pct = _pct(close, prev_close)

    high_20 = _num(recent["High"].max())
    low_20 = _num(recent["Low"].min())
    volume = int(_num(last.get("Volume"), 0))
    vol_ma5 = _num(last.get("VOL_MA5"), 0)
    vol_ma20 = _num(last.get("VOL_MA20"), 0)
    vol_vs_ma5 = _pct(volume, vol_ma5)
    vol_vs_ma20 = _pct(volume, vol_ma20)

    trend = _trend_label(last)
    risk = _risk_label(last)
    recent_table = _format_recent_rows(df, rows=20)

    return f"""# {symbol} AI 技術戰報

> 資料時間：{last.get("ts", "-")}
> 資料筆數：{len(df)} 筆，以下重點以最近 20 筆 K 線為主。

## 1. 快速結論
- 目前判讀：**{trend}**
- 最新收盤：**{close}**
- 單根變化：**{change} ({change_pct}%)**
- 20 筆區間：高點 **{high_20}** / 低點 **{low_20}**
- 主要風險：{risk}

## 2. 價格與均線
| 指標 | 數值 | 解讀 |
| :--- | ---: | :--- |
| Close | {close} | 最新收盤價 |
| MA5 | {_num(last.get("MA5"))} | 短線均線 |
| MA20 | {_num(last.get("MA20"))} | 中短線均線 |
| MA60 | {_num(last.get("MA60"))} | 中期均線 |
| MA120 | {_num(last.get("MA120"))} | 長期均線 |

## 3. 動能指標
| 指標 | 數值 | 解讀 |
| :--- | ---: | :--- |
| RSI14 | {_num(last.get("RSI"))} | 70 以上偏熱，30 以下偏弱 |
| MACD | {_num(last.get("MACD"))} | 快慢線差 |
| MACD Signal | {_num(last.get("MACD_SIGNAL"))} | 訊號線 |
| MACD Hist | {_num(last.get("MACD_HIST"))} | 大於 0 偏多，小於 0 偏空 |
| K | {_num(last.get("K"))} | KD K 值 |
| D | {_num(last.get("D"))} | KD D 值 |
| CCI20 | {_num(last.get("CCI"))} | 正值偏強，負值偏弱 |

## 4. 量能與波動
| 指標 | 數值 |
| :--- | ---: |
| 最新量 | {volume} |
| VOL MA5 | {vol_ma5} |
| VOL MA20 | {vol_ma20} |
| 量 vs MA5 | {vol_vs_ma5}% |
| 量 vs MA20 | {vol_vs_ma20}% |
| ATR14 | {_num(last.get("ATR14"))} |
| BB Upper | {_num(last.get("BB_UPPER"))} |
| BB Mid | {_num(last.get("BB_MID"))} |
| BB Lower | {_num(last.get("BB_LOWER"))} |
| BB Width | {_num(last.get("BB_WIDTH"), 4)} |

## 5. 支撐與壓力
| 類型 | 第一 | 第二 | 第三 |
| :--- | ---: | ---: | ---: |
| 支撐 | {_num(last.get("SUPPORT_1"))} | {_num(last.get("SUPPORT_2"))} | {_num(last.get("SUPPORT_3"))} |
| 壓力 | {_num(last.get("RESIST_1"))} | {_num(last.get("RESIST_2"))} | {_num(last.get("RESIST_3"))} |

## 6. 最近 20 筆資料
{recent_table}

## 7. MVP 操作提示
- 偏多情境：收盤站上 MA5/MA20 且 MACD Hist 轉正，可觀察是否有量能放大。
- 偏空情境：跌破 MA20 且 RSI 走弱，優先控管風險。
- 震盪情境：價格卡在支撐壓力之間，等突破或跌破後再判斷方向。
"""

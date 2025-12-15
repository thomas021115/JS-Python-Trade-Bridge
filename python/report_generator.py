def generate_ai_markdown(symbol, df):
    """
    產生給 LLM 閱讀的 Markdown 字串
    """
    if df.empty:
        return "無資料"

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    # 判斷漲跌
    change = last_row['Close'] - prev_row['Close']
    change_emoji = "🔺" if change > 0 else "🔻" if change < 0 else "➖"

    md_content = f"""
# 📊 股市戰情分析: {symbol}
> 資料時間: {last_row['ts']}

## 1. 核心數據快照
- **收盤價**: {last_row['Close']} {change_emoji} ({change})
- **成交量**: {last_row['Volume']}
- **MA5 (短線)**: {last_row['MA5']:.2f}
- **MA20 (月線)**: {last_row['MA20']:.2f}

## 2. 技術指標狀態
| 指標 | 數值 | 訊號解讀 |
| :--- | :--- | :--- |
| RSI (14) | {last_row['RSI']:.2f} | {'🔥 過熱 (小心回檔)' if last_row['RSI'] > 70 else '❄️ 超賣 (反彈機會)' if last_row['RSI'] < 30 else '😐 中立震盪'} |
| 趨勢判定 | - | {'📈 多頭排列 (強勢)' if last_row['MA5'] > last_row['MA20'] else '📉 空頭排列 (弱勢)'} |

## 3. 給 AI 的指令 (Prompt)
請扮演一位資深華爾街操盤手，根據以上數據：
1. 分析目前多空力道。
2. 預測未來 3 天可能的走勢。
3. 給出操作建議 (Buy / Sell / Hold)。
    """
    return md_content
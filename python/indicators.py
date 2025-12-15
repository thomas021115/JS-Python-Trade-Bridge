import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    # 使用 Wilder 的平滑移動平均 (RSI 標準算法)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_indicators(df):
    """
    幫 DataFrame 加上技術指標 (純 Pandas 實作版，相容性高)
    """
    # 複製一份以免動到原始資料
    df = df.copy()
    
    # 確保 Close 是浮點數
    df['Close'] = df['Close'].astype(float)
    
    # 計算 RSI (14)
    df['RSI'] = calculate_rsi(df['Close'], period=14)
    
    # 計算 SMA (5, 20)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # 填補 NaN (前幾筆算不出指標的會變成 0)
    df.fillna(0, inplace=True)
    
    return df
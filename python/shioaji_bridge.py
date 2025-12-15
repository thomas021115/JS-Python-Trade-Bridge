import shioaji as sj
import pandas as pd
import os
from dotenv import load_dotenv
import datetime
import time

load_dotenv()


class ShioajiBridge:
    def __init__(self):
        self.api = sj.Shioaji(simulation=False)
        self.is_connected = False

    def login(self):
        if self.is_connected:
            return

        try:
            self.api.login(
                api_key=os.getenv("API_KEY"),
                secret_key=os.getenv("SECRET_KEY"),
                fetch_contract=False,
            )
            self.api.fetch_contracts(contract_download=True)
            print(">>> Shioaji 登入成功 (正式模式)")
            self.is_connected = True
        except Exception as e:
            print(f">>> 登入失敗: {e}")
            self.is_connected = False

    def get_kbars(self, contract_code: str):
        # 1. 確保已連線
        if not self.is_connected:
            self.login()

        # 2. 確保合約已抓到 (重試機制)
        contract = None
        for _ in range(3): # 嘗試 3 次
            try:
                contract = self.api.Contracts.Stocks[contract_code]
                break
            except Exception:
                print(f"等待合約下載中... (retry for {contract_code})")
                time.sleep(1)
        
        if contract is None:
            print(f"❌ 錯誤: 找不到合約 {contract_code}，可能是合約下載未完成")
            return None

        print(f"✅ 取得合約: {contract.name} ({contract.code})")

        # 3. 擴大日期範圍 (抓 30 天，確保避開連假或沒資料的日子)
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=30)).isoformat()
        end_date = (today + datetime.timedelta(days=1)).isoformat()

        print(f"🔍 正在抓取範圍: {start_date} ~ {end_date}")

        try:
            # 抓取資料
            kbars = self.api.kbars(contract, start=start_date, end=end_date)
            
            # 4. 強制轉換資料格式 (最穩定的寫法)
            df = pd.DataFrame({
                "ts": pd.to_datetime(kbars.ts),
                "Open": kbars.Open,
                "High": kbars.High,
                "Low": kbars.Low,
                "Close": kbars.Close,
                "Volume": kbars.Volume
            })

            # 過濾空資料
            if df.empty:
                print("❌ 資料庫回傳空值 (Empty DataFrame)")
                return None
            
            # 轉換數值型態 (防呆)
            df['Close'] = df['Close'].astype(float)
            df['Volume'] = df['Volume'].astype(int)

            print(f"🎉 成功抓取 {len(df)} 筆資料！")
            return df

        except Exception as e:
            print(f"❌ 抓取或轉換過程失敗: {e}")
            return None

bridge = ShioajiBridge()
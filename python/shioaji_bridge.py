import shioaji as sj
import pandas as pd
import os
from dotenv import load_dotenv
import datetime

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
        if not self.is_connected:
            self.login()

        contract = self.api.Contracts.Stocks[contract_code]

        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=5)).isoformat()
        end_date = (today + datetime.timedelta(days=1)).isoformat()

    
        kbars = self.api.kbars(contract, start=start_date, end=end_date)

        # ✅ 關鍵：kbars 可能是 list/iterable of (key, list)，先轉 dict
        if not isinstance(kbars, dict):
            kbars = dict(kbars)

        df = pd.DataFrame(kbars)

        # ✅ 防呆：如果還是不小心變成 (7,2) 的怪格式，就再轉一次
        if df.shape[1] == 2 and list(df.columns) == [0, 1]:
            kbars2 = dict(zip(df[0], df[1]))
            df = pd.DataFrame(kbars2)

        if df.empty:
            return None

        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"])
        elif "t" in df.columns:
            df["t"] = pd.to_datetime(df["t"])

bridge = ShioajiBridge()

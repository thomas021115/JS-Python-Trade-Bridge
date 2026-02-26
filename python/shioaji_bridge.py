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


# 儀表板頁面(portfolio)
    def get_positions(self):
        # 嘗試連線
        if not self.is_connected:
            self.login()

        # 開始抓資料
        try:
            positions=self.api.list_positions(unit=sj.constant.Unit.Share)
            if not positions:
                return []
                
            # 抓取股票資訊
            contracts = []
            for p in positions:
                try:
                    c=self.api.Contracts.Stocks[p.code]
                    contracts.append(c)
                except Exception:
                    print(f"❌ 無法取得合約資料: {p.code}")

            # 快速查價 (Snapshots)
            price_map = {}
            if contracts:
                snapshot = self.api.snapshots(contracts)
                for s in snapshot:
                    price_map[s.code]=s.close

                # 計算損益和整理格式
                result = []
                for p in positions:
                    code = p.code
                    name = code 
                    
                    # 嘗試取得中文名稱
                    if code in self.api.Contracts.Stocks:
                        name = self.api.Contracts.Stocks[code].name
                    quantity = int(p.quantity) # 持股數
                    cost_price = float(p.price) # 平均成本
                    # 取得現價 (如果快照沒抓到，暫時用成本價代替，避免程式崩潰)
                    current_price = price_map.get(code, cost_price)
                    
                    # 損益計算核心
                    # 市值 = 股數 * 現價
                    market_value = int(quantity * current_price)
                    # 總成本 = 股數 * 平均成本
                    total_cost = int(quantity * cost_price)
                    
                    # 未實現損益
                    pnl = market_value - total_cost
                    
                    # 報酬率 (%)
                    if total_cost != 0:
                        pnl_rate = round((pnl / total_cost) * 100, 2)
                    else:
                        pnl_rate = 0.0

                    result.append({
                        "code": code,
                        "name": name,
                        "quantity": quantity,
                        "price": cost_price,
                        "current_price": current_price,
                        "pnl": pnl,
                        "pnl_rate": pnl_rate
                    })
                
                print(f"✅ 成功取得 {len(result)} 檔庫存損益資訊")
                return result

        except Exception as e:
                print(f"❌ 取得庫存失敗: {e}")
                # 出錯時回傳空陣列，避免前端掛掉
                return []        

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
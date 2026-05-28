import datetime
import os
import time

import pandas as pd
import shioaji as sj
from dotenv import load_dotenv

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
            print(">>> Shioaji login success")
            self.is_connected = True
        except Exception as e:
            print(f">>> Shioaji login failed: {e}")
            self.is_connected = False

    def logout(self):
        if not self.is_connected:
            return

        self.api.logout()
        self.is_connected = False

    def _ensure_connected(self):
        if not self.is_connected:
            self.login()

        if not self.is_connected:
            raise RuntimeError("shioaji_not_connected")

    def _enum_value(self, value):
        if value is None:
            return None
        if hasattr(value, "value"):
            return value.value
        if hasattr(value, "name"):
            return value.name
        return str(value)

    def _stock_name(self, code: str):
        try:
            contract = self.api.Contracts.Stocks[code]
            return getattr(contract, "name", None)
        except Exception:
            return None

    def get_kbars(self, contract_code: str, start: str | None = None, end: str | None = None):
        self._ensure_connected()

        contract = None
        for _ in range(2):
            try:
                contract = self.api.Contracts.Stocks[contract_code]
                break
            except Exception:
                print(f"Waiting for contract: {contract_code}")
                time.sleep(1)

        if contract is None:
            print(f"Contract not found: {contract_code}")
            return None

        print(f"Contract loaded: {contract.name} ({contract.code})")

        today = datetime.date.today()
        start_date = start or (today - datetime.timedelta(days=30)).isoformat()
        end_date = end or (today + datetime.timedelta(days=1)).isoformat()

        started_at = time.perf_counter()
        started_time = datetime.datetime.now().isoformat(timespec="seconds")
        print(f"Fetching kbars start: code={contract_code}, start={start_date}, end={end_date}, at={started_time}")

        try:
            kbars = self.api.kbars(contract, start=start_date, end=end_date)
            df = pd.DataFrame({
                "ts": pd.to_datetime(kbars.ts),
                "Open": kbars.Open,
                "High": kbars.High,
                "Low": kbars.Low,
                "Close": kbars.Close,
                "Volume": kbars.Volume,
            })

            if df.empty:
                elapsed = time.perf_counter() - started_at
                print(f"Fetching kbars empty: code={contract_code}, elapsed={elapsed:.2f}s")
                return None

            df["Close"] = df["Close"].astype(float)
            df["Volume"] = df["Volume"].astype(int)

            elapsed = time.perf_counter() - started_at
            print(f"Fetching kbars done: code={contract_code}, rows={len(df)}, elapsed={elapsed:.2f}s")
            return df

        except Exception as e:
            elapsed = time.perf_counter() - started_at
            print(f"Fetching kbars failed: code={contract_code}, elapsed={elapsed:.2f}s, error={e}")
            return None

    def get_stock_positions(self):
        self._ensure_connected()

        positions = self.api.list_positions(
            self.api.stock_account,
            unit=sj.constant.Unit.Share,
        )
        rows = []

        for position in positions:
            print("[Shioaji position raw]", getattr(position, "__dict__", position))

            code = str(getattr(position, "code", ""))
            quantity = int(getattr(position, "quantity", 0) or 0)
            yd_quantity = int(getattr(position, "yd_quantity", 0) or 0)
            display_quantity = quantity or yd_quantity
            price = float(getattr(position, "price", 0) or 0)
            last_price = float(getattr(position, "last_price", 0) or 0)
            pnl = float(getattr(position, "pnl", 0) or 0)
            cost = display_quantity * price
            market_value = display_quantity * last_price

            rows.append({
                "id": int(getattr(position, "id", 0) or 0),
                "code": code,
                "name": self._stock_name(code),
                "direction": self._enum_value(getattr(position, "direction", None)),
                "quantity": display_quantity,
                "yd_quantity": yd_quantity,
                "price": price,
                "last_price": last_price,
                "pnl": pnl,
                "pnl_rate": round((pnl / cost) * 100, 2) if cost else 0.0,
                "market_value": round(market_value, 2),
                "cond": self._enum_value(getattr(position, "cond", None)),
            })

        return rows


bridge = ShioajiBridge()

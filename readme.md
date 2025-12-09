# JS-Python-Trade-Bridge  
> A Full-Stack Trading Data Bridge using **Python Shioaji** + **FastAPI** + **Node.js**  
> 提供 Shioaji 正式 API 的金融資料，給 JavaScript / Node.js 使用。

---

##  專案介紹

永豐金 Shioaji API **只有 Python 版本**，JavaScript/Node.js 無法直接登入、抓 K 線、或訂閱行情。  
本專案解決這個問題：

###  使用 Python（Shioaji）登入正式 API  
###  使用 FastAPI 建立本地 API Server  
###  JavaScript/Node.js 可以用 fetch / axios 直接取得金融資料  
###  支援：K 線、Tick、五檔、商品資訊、委託測試  

這是一個 **JS 與 Python 的金融資料橋接器（Bridge）**，  
讓 JS 前後端可以使用永豐金的正式金融資料。

---

##  功能 (Features)

Python Shioaji 正式 API 連線 | 使用 simulation=False + signed=True |
抓取日 K / 1 分 K / 5 分 K | 提供 JavaScript 可用的 JSON 格式 |
即時 Tick 訂閱 | 由 Python 推送 |
五檔委託簿（Order Book） | 提供市場深度資料 |
FastAPI REST API | Node.js 可直接呼叫 |
支援多股票查詢 | 可用 query string 控制 |
後續可擴充寫入資料庫 | MySQL / PostgreSQL / MongoDB |

---

## 🏗 系統架構 (Architecture)

以下為本專案的資料流：

```mermaid
flowchart LR
    A[Shioaji API<br/>Python] -->|K線 / Tick / 五檔| B[FastAPI Server]
    B -->|HTTP REST| C[Node.js / Next.js 前端]
    C -->|顯示圖表 / 分析| D[使用者介面]

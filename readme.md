# JS-Python-Trade-Bridge

> A production-oriented bridge that exposes **Shioaji (Python-only)** market data to JavaScript apps via **FastAPI**.

---

## 1) Project Goal

Shioaji only provides a Python SDK. This project makes that data available to:
- Web frontends (Vue/React/Next.js)
- Node.js backend services
- Internal quant tooling that prefers HTTP-based integration

Core idea:
1. Python connects to Shioaji.
2. FastAPI serves normalized REST responses.
3. JS/TS clients consume data via HTTP.

---

## 2) Current Scope (Deliverable Baseline)

- K-bar retrieval
- Technical indicator enrichment
- AI payload/report endpoints
- Data sync to MySQL
- Query from database snapshots

This baseline is intended to be **stable enough for handoff/demo/UAT**, and can be refactored iteratively for deeper maintainability.

---

## 3) Repository Structure

```text
.
├─ python/
│  ├─ app.py                # FastAPI entrypoint
│  ├─ shioaji_bridge.py     # Shioaji login/data fetch bridge
│  ├─ indicators.py         # Technical indicator calculations
│  ├─ db_repository.py      # SQL persistence/read helpers
│  ├─ database.py           # SQLAlchemy engine/session
│  ├─ models.py             # DB model definitions (if used)
│  ├─ report_generator.py   # AI markdown report generation
│  └─ requirements.txt
├─ web/
│  ├─ src/
│  └─ package.json
└─ readme.md
```

---

## 4) Backend Quick Start (Python/FastAPI)

### Prerequisites
- Python 3.10+
- MySQL 8+
- Valid Shioaji credentials/cert setup

### Install

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create `python/.env` (example):

```env
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=trade_bridge
```

> Add your Shioaji auth-related env vars/settings based on your local security setup.

### Run API

```bash
cd python
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

---

## 5) Frontend Quick Start (Vue)

```bash
cd web
npm install
npm run dev
```

Default dev URL: `http://127.0.0.1:5173`

---

## 6) API Snapshot (Baseline)

- `GET /` : service health
- `GET /api/kline/{symbol}` : latest enriched K-line rows
- `GET /api/ai-briefing/{code}` : compact AI briefing rows
- `GET /api/ai-report/{code}` : generated markdown report + DB save
- `GET /api/ai-payload/{symbol}` : structured indicator payload
- `POST /api/sync/{symbol}` : sync market+indicator data to DB
- `GET /api/db/kline/{symbol}?days=7` : read recent K-lines from DB
- `GET /api/test/db-kline/{symbol}?start=...&end=...` : DB range test
- `GET /api/test/kbars/{symbol}?start=...&end=...` : remote source test

---

## 7) Delivery Notes (for Formal Handoff)

For a formal deliverable package, ensure:
- `.env` is provided via secure channel (never commit secrets).
- DB schema and indexes are applied in target environment.
- UAT checklist includes at least one real symbol end-to-end run:
  - Source fetch
  - Indicator generation
  - DB sync
  - API readback
- API consumer contract is frozen for the current milestone.

---

## 8) Next Iteration (Maintainability Upgrade Plan)

Recommended incremental improvements (without breaking contract):
1. Split `app.py` into routers/services.
2. Add Pydantic request/response models.
3. Standardize error response format and HTTP status usage.
4. Add unit/integration tests with pytest.
5. Add CI for lint/test and migration checks.

This keeps current delivery usable, while reducing future maintenance cost.

# MVP E2E Smoke Test

## Test Date

- 2026-06-08

## Test Environment

- Python: 3.14.1
- pandas: 2.3.3
- MySQL: 8.0.44
- Test database: `trade_bridge_e2e_check`

## Verified Items

- Frontend build: `npm run build` OK
- Python app import: `python -c "import app; print('app import ok')"` OK
- Python compile check: `python -m compileall .` OK
- MySQL connection: OK
- `schema.sql` import to clean test DB: OK
- Uvicorn startup: OK
- Shioaji login: OK
- `POST /api/sync/2330?start_date=2026-05-01&end_date=2026-05-30`: OK
- `GET /api/ai-report/2330?start_date=2026-05-01&end_date=2026-05-30`: OK

## E2E Result Summary

`POST /api/sync/2330` completed successfully:

| Metric | Value |
| :--- | ---: |
| fetched_rows | 5319 |
| saved_1m_rows | 5319 |
| saved_1d_rows | 20 |
| saved_1w_rows | 4 |
| technical_snapshot_saved | 5319 |
| technical_snapshot_1d_saved | 20 |
| technical_snapshot_1w_saved | 4 |
| elapsed_seconds | 8.61 |

`GET /api/ai-report/2330` completed successfully:

| Metric | Value |
| :--- | ---: |
| saved | true |
| report_id | 1 |
| data_source | database |
| db_rows_used | 5319 |
| shioaji_rows_fetched | 0 |
| data_quality_warning | true |
| report_length | 166768 |

Final test DB row counts:

| Table | Rows |
| :--- | ---: |
| stocks | 1 |
| daily_price | 5343 |
| technical_snapshot | 5343 |
| ai_report | 1 |

## Safety Notes

- E2E write testing used only `trade_bridge_e2e_check`.
- The production/local working database `trade_bridge` was not used for E2E writes.
- No production table was dropped, truncated, deleted, or altered during the E2E flow.

## Conclusion

- MVP E2E smoke test passed.
- Current deliverability: about 90%.

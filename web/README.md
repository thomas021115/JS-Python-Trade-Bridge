# Web Client (Vue 3 + TypeScript + Vite)

This folder contains the frontend for JS-Python-Trade-Bridge.

## Purpose
- Consume FastAPI endpoints from `../python/app.py`
- Render market data, report output, and analysis pages
- Provide a lightweight UI for demo/UAT workflows

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm run preview
```

## Environment Notes
- Ensure backend is running (default: `http://127.0.0.1:8000`).
- Configure API base URL in frontend service config as needed.

## Suggested Next Steps
- Add environment-based API URL management.
- Add API error-state handling and retry UX.
- Add component/unit tests for key pages.

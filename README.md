# UAP NEXUS

Unified Aerospace Phenomena tracking platform for ingesting, processing, and visualizing government UAP disclosures.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run crawler (once)
python -m crawler.run --once

# Start API
uvicorn api.main:app --reload
```

## Architecture

```
uap-nexus/
├── crawler/      # PURSUE tracker (war.gov/UFO, AARO polling)
├── pipeline/      # OCR + AI extraction
├── api/           # FastAPI REST endpoints
├── frontend/      # React dashboard
└── ml/           # Pattern detection (Phase 3)
```

## API Endpoints

- `GET /api/health` — Health check
- `GET /api/incidents` — List incidents
- `GET /api/crawler/status` — Crawler status
- `POST /api/crawler/trigger` — Manual crawl

See full docs at `/api/docs`

## Deploy

See [render.yaml](render.yaml) for Render.com deployment config.
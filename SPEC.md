# UAP NEXUS - Specification

## Overview
Unified Aerospace Phenomena tracking platform for ingesting, processing, and visualizing government UAP disclosures.

## Tech Stack
- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL 15 + pgvector (vector embeddings)
- **Queue**: Redis + Celery (async job processing)
- **OCR**: AWS Textract
- **AI**: Claude API (structured extraction + vision)
- **Frontend**: React + Vite + Deck.gl
- **Maps**: Mapbox GL JS
- **Alerts**: Telegram Bot + Discord Webhooks + SendGrid
- **ML**: scikit-learn + UMAP + HDBSCAN
- **Container**: Docker Compose

## Module Structure

### Phase 1 (Week 1-2) - Foundation
- [x] **crawler/** - PURSUE tracker (war.gov/UFO, AARO.mil polling)
  - `scraper.py` - Site poller with rate limiting
  - `diff_engine.py` - Detect new document releases
  - `alert_dispatch.py` - Multi-channel alert routing
- [x] **pipeline/** - OCR + AI extraction
  - `ocr.py` - Textract integration
  - `extractor.py` - Claude structured extraction
  - `embedder.py` - pgvector embeddings
  - `schemas.py` - Pydantic models
- [x] **api/** - FastAPI REST endpoints
- [x] **models/** - SQLAlchemy + pgvector models

### Phase 2 (Month 1) - Visualization & Crossref
- [ ] **frontend/globe/** - Deck.gl 3D incident map
- [ ] **frontend/timeline/** - PURSUE release timeline
- [ ] **crossref/** - FOIA document cross-reference
- [ ] **vision/** - IR image classification

### Phase 3 (Month 2) - Community & Intelligence
- [ ] **ml/** - Pattern detection & clustering
- [ ] **frontend/submit/** - Civilian submission portal
- [ ] **frontend/newsletter/** - Auto-generated digests

## Data Model

### Incident
```
id: UUID (PK)
source: Enum[PURSUE, AARO, FOIA, CIVILIAN]
agency: String
incident_date: Date
release_date: Date
location_name: String
lat: Float
lon: Float
incident_type: String
craft_description: Text
witnesses: JSON
resolution: Enum[UNRESOLVED, RESOLVED, PENDING]
raw_doc_url: String
extracted_text: Text
embedding: Vector(1536)
is_new: Boolean
foia_matches: Array[UUID]
image_ids: Array[UUID]
tags: Array[String]
created_at: DateTime
updated_at: DateTime
```

### Document
```
id: UUID (PK)
incident_id: UUID (FK)
source_url: String
file_type: Enum[PDF, PNG, JPG, TXT]
file_path: String
ocr_text: Text
uploaded_at: DateTime
```

## API Endpoints

### Incidents
- `GET /api/incidents` - List with filters (source, era, agency, region)
- `GET /api/incidents/{id}` - Single incident detail
- `GET /api/incidents/search` - Semantic similarity search
- `POST /api/incidents` - Manual incident creation

### Documents
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Document detail
- `POST /api/documents/upload` - Upload new document

### Crawler
- `POST /api/crawler/trigger` - Manual crawl trigger
- `GET /api/crawler/status` - Crawler health status
- `GET /api/crawler/history` - Recent crawl activity

### Alerts
- `POST /api/alerts/subscribe` - Alert subscription
- `GET /api/alerts/channels` - Available alert channels

## Environment Variables
```
DATABASE_URL=postgresql://user:pass@localhost:5432/uapnexus
REDIS_URL=redis://localhost:6379/0
CLAUDE_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
TELEGRAM_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=...
SENDGRID_API_KEY=...
MAPBOX_TOKEN=...
```

## Docker Services
- `postgres` - PostgreSQL 15 with pgvector extension
- `redis` - Redis 7 for Celery queue
- `api` - FastAPI application
- `worker` - Celery worker for async jobs
- `frontend` - React dev server (optional in Phase 1)

## Crawler Configuration
- Poll interval: 30 minutes (configurable)
- Rate limiting: 1 request/second max
- Retry policy: 3 retries with exponential backoff
- User agent: UAP-NEXUS/1.0 (+contact@uapnexus.com)

## Alert Channels
1. **Telegram**: Instant notifications to subscribed channels
2. **Discord**: Webhook integration for server channels
3. **Email**: SendGrid for weekly digests

## Claude Extraction Schema
```json
{
  "incident_date": "YYYY-MM-DD or null",
  "agency": "string",
  "location": {"name": "string", "lat": float, "lon": float},
  "craft_description": "string",
  "witnesses": ["array of roles"],
  "anomalous_characteristics": ["array of strings"],
  "resolution": "UNRESOLVED|RESOLVED|UNKNOWN",
  "key_quotes": ["max 3 short quotes"]
}
```

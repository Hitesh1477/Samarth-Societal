# SAMARTH Backend

FastAPI backend for the **SAMARTH** (Societal Action for Managing And Resolving Transformative Hackathon) platform.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Validation | Pydantic v2 + pydantic-settings |
| Database | Supabase (PostgreSQL via REST) |
| Auth | Supabase Auth |
| AI | OpenAI GPT-4o (Stage 2+) |
| Server | Uvicorn |

## Setup

### 1. Prerequisites

- Python 3.11+
- A Supabase project (free tier is fine)

### 2. Create virtual environment

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your Supabase credentials
```

### 5. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Stage 1 (Foundation)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

### Stage 2+ (Coming)

| Method | Path | Description |
|---|---|---|
| POST | `/api/problems` | Submit a problem report |
| GET | `/api/problems` | List / filter reports |
| GET | `/api/problems/{id}` | Get a single report |
| POST | `/api/problems/{id}/analyze` | Run AI analysis |
| GET | `/api/problems/{id}/duplicates` | Duplicate cluster |
| GET | `/api/challenges` | List challenges |
| GET | `/api/challenges/{id}` | Challenge detail |
| GET | `/api/challenges/{id}/priority` | Priority score |
| GET | `/api/challenges/{id}/solver-matches` | Solver matches |
| POST | `/api/projects` | Create project |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Project detail |
| PUT | `/api/projects/{id}` | Update project |
| POST | `/api/projects/{id}/milestones` | Add milestone |
| PUT | `/api/milestones/{id}` | Update milestone |
| POST | `/api/projects/{id}/impact` | Add impact metric |
| GET | `/api/projects/{id}/impact` | Impact summary |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/dashboard` | Full dashboard analytics |
| GET | `/api/map/challenges` | Map challenges |

## Project Structure

```
backend/
├── app/
│   ├── main.py            ← FastAPI app factory + CORS
│   ├── core/
│   │   ├── config.py      ← pydantic-settings (all env vars)
│   │   └── database.py    ← Supabase client factory
│   ├── schemas/
│   │   ├── base.py        ← CamelModel (auto camelCase serialisation)
│   │   ├── enums.py       ← All enums mirroring frontend types
│   │   └── common.py      ← Shared sub-schemas
│   ├── api/
│   │   └── health.py      ← GET /health
│   └── services/          ← Business logic (Stage 2+)
├── requirements.txt
├── .env.example
└── README.md
```

## camelCase Serialisation

The frontend expects camelCase field names (`affectedPopulation`, `createdAt`, etc.).
All Pydantic schemas inherit from `CamelModel` which uses `alias_generator=to_camel`,
so snake_case Python fields are automatically serialised to camelCase in every response.

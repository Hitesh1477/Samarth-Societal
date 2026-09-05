# SAMARTH — Societal Challenge & Innovation Platform

An AI-powered civic-tech platform that transforms community-reported problems into structured, prioritized societal challenges and connects them with universities, faculty, student teams, and industry partners.

**"We don't just collect complaints. We convert real-world problems into measurable solutions."**

## Core Journey

```
Citizen Problem Report → AI Problem Analysis → Duplicate Detection → Unified Challenge
→ Explainable Priority Score → Smart Solver Matching → Solution Workspace → Pilot → Measurable Impact
```

## Tech Stack

- **React** + **Vite** + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** component library
- **React Router** for navigation
- **Recharts** for data visualizations
- **React Leaflet** / **Leaflet** for geospatial maps
- **Supabase JavaScript client** for authentication and file uploads
- **FastAPI** (external) for AI analysis, problem structuring, duplicate detection, priority scoring, solver matching, and impact calculations

## Getting Started

```bash
# Install dependencies
npm install --legacy-peer-deps

# Start the dev server
npm run dev

# Build for production
npm run build
```

> **Note:** Use `--legacy-peer-deps` because `react-leaflet@4` has peer dependency constraints with React 18.

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Supabase
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# FastAPI backend (leave empty to use mock mode)
VITE_API_BASE_URL=http://localhost:8000

# Set to "true" only when VITE_API_BASE_URL is empty
VITE_USE_MOCK_API=false
```

## Mock Mode

The frontend works **even when the FastAPI backend is not running**. When `VITE_API_BASE_URL` is empty, API calls return realistic mock data with simulated delays. This allows full frontend development before backend integration. A configured API base URL always selects the real backend, even if a stale mock flag is present.

The UI uses the exact same response structures for mock and real API — switching between them requires no code changes.

## Connecting the FastAPI Backend

1. Set `VITE_USE_MOCK_API=false` in your `.env`
2. Set `VITE_API_BASE_URL` to your FastAPI server URL (e.g., `http://localhost:8000`)
3. The API service (`src/services/api.ts`) will automatically route all requests through the real backend

### API Endpoints Expected

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/problems` | Submit a new problem |
| GET | `/api/problems/{id}` | Get a single problem |
| GET | `/api/problems` | List problems (with filters) |
| POST | `/api/problems/{id}/analyze` | Trigger AI analysis |
| GET | `/api/problems/{id}/duplicates` | Get duplicate cluster |
| GET | `/api/challenges` | List challenges (with filters) |
| GET | `/api/challenges/{id}` | Get challenge details |
| GET | `/api/challenges/{id}/priority` | Get priority score |
| GET | `/api/challenges/{id}/solver-matches` | Get AI solver matches |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| PUT | `/api/projects/{id}` | Update a project |
| POST | `/api/projects/{id}/milestones` | Create a milestone |
| PUT | `/api/milestones/{id}` | Update a milestone |
| POST | `/api/projects/{id}/impact` | Add impact metric |
| GET | `/api/projects/{id}/impact` | Get impact summary |
| GET | `/api/dashboard` | Get dashboard analytics and statistics |
| GET | `/api/map/challenges` | Get map challenge data |

## Supabase Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Copy your project URL and anon key from Settings > API
3. Add them to `.env` as `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
4. Supabase is used for:
   - **Authentication** (email/password sign-in and registration)
   - **Session persistence** (automatic token refresh)
   - **File/image uploads** (Storage buckets for evidence photos)

## Project Structure

```
src/
├── components/
│   ├── layout/          # AppLayout, Sidebar, TopNav
│   ├── shared/          # StatCard, Badges
│   ├── ui/              # shadcn/ui components
│   └── ProtectedRoute.tsx
├── hooks/
│   └── use-auth.tsx     # Auth context + Supabase integration
├── lib/
│   ├── supabase.ts      # Supabase client
│   ├── helpers.ts       # Status/priority helpers, date formatting
│   └── utils.ts         # cn() utility
├── pages/
│   ├── LandingPage.tsx
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── ReportProblemPage.tsx
│   ├── AIAnalysisPage.tsx
│   ├── DashboardPage.tsx
│   ├── ProblemsPage.tsx
│   ├── ChallengesPage.tsx
│   ├── ChallengeDetailPage.tsx
│   ├── MapPage.tsx
│   ├── SolverMatchingPage.tsx
│   ├── ProjectsPage.tsx
│   ├── ProjectDetailPage.tsx
│   ├── ImpactDashboardPage.tsx
│   └── AnalyticsPage.tsx
├── services/
│   ├── api.ts           # API service layer (mock + real)
│   └── mockData.ts      # All mock/demo data
├── types/
│   └── index.ts         # Centralized TypeScript interfaces
├── App.tsx              # Routes
└── main.tsx             # Entry point
```

## User Roles

- **CITIZEN** — Report problems, track reports, view impact
- **GOVERNMENT** — Validate and prioritize challenges
- **UNIVERSITY** — Propose solutions, manage teams
- **FACULTY** — Mentor student teams
- **STUDENT** — Build solutions
- **INDUSTRY** — Partner on pilots and implementation
- **ADMIN** — Full dashboard and platform oversight

## Demo Data

The primary demo challenge is **"Urban Road Waterlogging – Ranchi"**:
- 20 citizen reports merged into 1 unified challenge
- Priority score: 87/100 (HIGH)
- Affected population: 2,500
- University match: XYZ Institute of Technology (94%)
- Industry match: ABC Infrastructure Solutions (89%)
- Solution: Smart drainage redesign + road elevation
- Impact: Road accessibility 40% → 95%, waterlogging 8h → 1.5h

Built for Smart India Hackathon.

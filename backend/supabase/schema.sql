-- =============================================================================
-- SAMARTH Platform — MVP Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- =============================================================================

-- Enable pgvector (used in Stage 3 for AI embedding similarity search)
-- Safe to run even if already enabled; will no-op if unavailable.
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- PROFILES
-- Extends Supabase auth.users with role and display info.
-- =============================================================================

CREATE TABLE IF NOT EXISTS profiles (
    id           UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name         TEXT NOT NULL DEFAULT '',
    role         TEXT NOT NULL DEFAULT 'CITIZEN'
                     CHECK (role IN ('CITIZEN','GOVERNMENT','UNIVERSITY','FACULTY','STUDENT','INDUSTRY','ADMIN')),
    avatar_url   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create the application profile in the same transaction as auth.users.
-- Signup metadata is supplied by the frontend through supabase.auth.signUp().
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    requested_role TEXT;
BEGIN
    requested_role := UPPER(COALESCE(NEW.raw_user_meta_data ->> 'role', 'CITIZEN'));

    IF requested_role NOT IN (
        'CITIZEN', 'GOVERNMENT', 'UNIVERSITY', 'FACULTY',
        'STUDENT', 'INDUSTRY', 'ADMIN'
    ) THEN
        requested_role := 'CITIZEN';
    END IF;

    INSERT INTO public.profiles (id, name, role, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(
            NULLIF(BTRIM(NEW.raw_user_meta_data ->> 'name'), ''),
            NULLIF(SPLIT_PART(COALESCE(NEW.email, ''), '@', 1), ''),
            ''
        ),
        requested_role,
        NULLIF(BTRIM(NEW.raw_user_meta_data ->> 'avatar_url'), '')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- ORGANIZATIONS
-- Universities, government bodies, NGOs, industry partners.
-- =============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT NOT NULL,
    type         TEXT NOT NULL DEFAULT 'OTHER'
                     CHECK (type IN ('UNIVERSITY','GOVERNMENT','INDUSTRY','NGO','OTHER')),
    district     TEXT,
    state        TEXT,
    contact_email TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- CHALLENGES
-- A validated, unified problem cluster (aggregates many citizen reports).
-- Created in Stage 3+ when AI analysis detects clustering.
-- Defined early so problems.challenge_id FK works from day 1.
-- =============================================================================

CREATE TABLE IF NOT EXISTS challenges (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title               TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    category            TEXT NOT NULL,
    subcategory         TEXT NOT NULL DEFAULT '',
    district            TEXT NOT NULL DEFAULT '',
    location_name       TEXT NOT NULL DEFAULT '',
    lat                 DOUBLE PRECISION NOT NULL DEFAULT 0,
    lng                 DOUBLE PRECISION NOT NULL DEFAULT 0,
    report_count        INTEGER NOT NULL DEFAULT 0,
    affected_population INTEGER NOT NULL DEFAULT 0,
    priority            NUMERIC(5,2) NOT NULL DEFAULT 0,
    priority_level      TEXT NOT NULL DEFAULT 'LOW'
                            CHECK (priority_level IN ('HIGH','MEDIUM','LOW')),
    status              TEXT NOT NULL DEFAULT 'NEW'
                            CHECK (status IN (
                                'NEW','UNDER_VALIDATION','PRIORITIZED',
                                'MATCHED','SOLUTION_PROPOSED','PILOT','COMPLETED'
                            )),
    assigned_solver     TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_challenges_status   ON challenges(status);
CREATE INDEX IF NOT EXISTS idx_challenges_category ON challenges(category);
CREATE INDEX IF NOT EXISTS idx_challenges_district ON challenges(district);

-- =============================================================================
-- PROJECTS
-- A solution workspace linked to a challenge.
-- =============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    challenge_id     UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    challenge_title  TEXT NOT NULL DEFAULT '',
    title            TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'PROPOSAL'
                         CHECK (status IN ('PROPOSAL','ACTIVE','PILOT','COMPLETED')),
    progress         NUMERIC(5,2) NOT NULL DEFAULT 0
                         CHECK (progress >= 0 AND progress <= 100),
    team             JSONB NOT NULL DEFAULT '[]'::jsonb,
    faculty_mentor   TEXT NOT NULL DEFAULT '',
    industry_partner TEXT NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_challenge_id ON projects(challenge_id);
CREATE INDEX IF NOT EXISTS idx_projects_status       ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at   ON projects(created_at DESC);

-- =============================================================================
-- MILESTONES
-- Progress checkpoints belonging to a solution project.
-- =============================================================================

CREATE TABLE IF NOT EXISTS milestones (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title          TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','in_progress','completed')),
    progress       NUMERIC(5,2) NOT NULL DEFAULT 0
                       CHECK (progress >= 0 AND progress <= 100),
    due_date       TEXT NOT NULL DEFAULT '',
    evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestones_project_id ON milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status     ON milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_created_at ON milestones(created_at DESC);

-- =============================================================================
-- IMPACT METRICS
-- Before/after measurements belonging to a project.
-- =============================================================================

CREATE TABLE IF NOT EXISTS impact_metrics (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    label      TEXT NOT NULL,
    before     DOUBLE PRECISION NOT NULL,
    after      DOUBLE PRECISION NOT NULL,
    unit       TEXT NOT NULL DEFAULT '',
    improvement DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_impact_metrics_project_id ON impact_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_impact_metrics_created_at ON impact_metrics(created_at DESC);

-- =============================================================================
-- PROBLEMS
-- A raw citizen-submitted report.
-- =============================================================================

CREATE TABLE IF NOT EXISTS problems (
    -- Identity
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    category            TEXT NOT NULL
                            CHECK (category IN (
                                'Infrastructure','Water & Sanitation','Healthcare',
                                'Education','Agriculture','Environment',
                                'Public Safety','Transport','Waste Management','Other'
                            )),
    subcategory         TEXT NOT NULL DEFAULT '',
    urgency             TEXT NOT NULL DEFAULT 'MEDIUM'
                            CHECK (urgency IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    affected_population INTEGER NOT NULL DEFAULT 0 CHECK (affected_population >= 0),

    -- Location (flat columns for indexed filtering; no JSONB needed here)
    location_lat        DOUBLE PRECISION NOT NULL,
    location_lng        DOUBLE PRECISION NOT NULL,
    location_name       TEXT NOT NULL DEFAULT '',
    location_district   TEXT NOT NULL DEFAULT '',

    -- Reporter (anonymous for MVP — no auth required to submit)
    reporter_name       TEXT NOT NULL DEFAULT '',
    -- Supabase Auth user ID of the submitting citizen (NULL for anonymous / legacy records)
    reporter_id         TEXT,

    -- Workflow
    status              TEXT NOT NULL DEFAULT 'SUBMITTED'
                            CHECK (status IN ('SUBMITTED','ANALYZED','MERGED')),
    challenge_id        UUID REFERENCES challenges(id) ON DELETE SET NULL,
    similarity          NUMERIC(5,4),   -- 0.0000–1.0000, NULL until AI runs
    distance            TEXT,           -- human-readable, e.g. "0.3 km"

    -- AI embedding (Stage 3 — NULL until analyzed)
    embedding           vector(1536),

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for the frontend filter params: category, district, status
CREATE INDEX IF NOT EXISTS idx_problems_category         ON problems(category);
CREATE INDEX IF NOT EXISTS idx_problems_district         ON problems(location_district);
CREATE INDEX IF NOT EXISTS idx_problems_status           ON problems(status);
CREATE INDEX IF NOT EXISTS idx_problems_created_at       ON problems(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_problems_challenge_id     ON problems(challenge_id);
CREATE INDEX IF NOT EXISTS idx_problems_reporter_id      ON problems(reporter_id);

-- Full-text search index on title + description
CREATE INDEX IF NOT EXISTS idx_problems_fts ON problems
    USING GIN (to_tsvector('english', title || ' ' || description));

-- =============================================================================
-- PROBLEM EVIDENCE
-- Files (images, audio, documents) attached to a problem report.
-- =============================================================================

CREATE TABLE IF NOT EXISTS problem_evidence (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id  UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('image','audio','document')),
    url         TEXT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_problem_id ON problem_evidence(problem_id);

-- =============================================================================
-- PROBLEM CLUSTERS
-- Tracks which problems have been grouped together (pre-challenge).
-- Created by Stage 3 duplicate detection.
-- =============================================================================

CREATE TABLE IF NOT EXISTS problem_clusters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    clustered_problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5,4) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (primary_problem_id, clustered_problem_id)
);

CREATE INDEX IF NOT EXISTS idx_clusters_primary    ON problem_clusters(primary_problem_id);
CREATE INDEX IF NOT EXISTS idx_clusters_clustered  ON problem_clusters(clustered_problem_id);

-- =============================================================================
-- SOLVER PROFILES
-- Academic departments, R&D labs, and industry partners available for matching.
-- =============================================================================

CREATE TABLE IF NOT EXISTS solver_profiles (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    type              TEXT NOT NULL CHECK (type IN ('university','industry')),
    department        TEXT,
    district          TEXT NOT NULL DEFAULT '',
    state             TEXT NOT NULL DEFAULT '',
    categories        TEXT[] NOT NULL DEFAULT '{}',
    expertise         TEXT[] NOT NULL DEFAULT '{}',
    capacity          TEXT NOT NULL DEFAULT 'HIGH' CHECK (capacity IN ('HIGH','MEDIUM','LOW')),
    equipment         TEXT[] NOT NULL DEFAULT '{}',
    previous_projects TEXT[] NOT NULL DEFAULT '{}',
    description       TEXT NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_solver_profiles_type ON solver_profiles(type);
CREATE INDEX IF NOT EXISTS idx_solver_profiles_district ON solver_profiles(district);

-- =============================================================================
-- ROW-LEVEL SECURITY (RLS)
-- Enable but keep permissive for MVP — tighten in production.
-- =============================================================================

ALTER TABLE profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE problems         ENABLE ROW LEVEL SECURITY;
ALTER TABLE problem_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE problem_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenges       ENABLE ROW LEVEL SECURITY;
ALTER TABLE solver_profiles  ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects         ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones        ENABLE ROW LEVEL SECURITY;
ALTER TABLE impact_metrics    ENABLE ROW LEVEL SECURITY;

-- Public read on problems, challenges, and solver_profiles
CREATE POLICY "Public read problems"        ON problems        FOR SELECT USING (true);
CREATE POLICY "Public read challenges"      ON challenges      FOR SELECT USING (true);
CREATE POLICY "Public read evidence"        ON problem_evidence FOR SELECT USING (true);
CREATE POLICY "Public read solver_profiles" ON solver_profiles FOR SELECT USING (true);
CREATE POLICY "Public read projects"        ON projects       FOR SELECT USING (true);
CREATE POLICY "Public read milestones"       ON milestones      FOR SELECT USING (true);
CREATE POLICY "Public read impact_metrics"   ON impact_metrics  FOR SELECT USING (true);

-- Anyone can submit a problem (anonymous reports allowed in MVP)
CREATE POLICY "Public insert problems" ON problems     FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert evidence" ON problem_evidence FOR INSERT WITH CHECK (true);

-- Service role can do everything (backend uses service role key for mutations)
-- This is handled implicitly: service role bypasses RLS.

-- =============================================================================
-- UPDATED_AT TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER set_problems_updated_at
    BEFORE UPDATE ON problems
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_challenges_updated_at
    BEFORE UPDATE ON challenges
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

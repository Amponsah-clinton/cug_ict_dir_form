-- ============================================================
-- CUG Archival System — Supabase SQL Migrations
-- Run in: https://supabase.com/dashboard/project/xdouuloczyuaqplfmrve/sql
-- Safe to re-run (uses IF NOT EXISTS / IF EXISTS guards)
-- ============================================================

-- ── 1. Correction checkbox state ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cug_corrections (
    id              BIGSERIAL    PRIMARY KEY,
    correction_id   TEXT         NOT NULL UNIQUE,   -- e.g. "s1_01"
    is_done         BOOLEAN      NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION _cug_corrections_set_updated()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_cug_corrections_updated ON cug_corrections;
CREATE TRIGGER trg_cug_corrections_updated
    BEFORE UPDATE ON cug_corrections
    FOR EACH ROW EXECUTE FUNCTION _cug_corrections_set_updated();


-- ── 2. Director confirmation (name + date + drawn signature PNG) ──────────────
CREATE TABLE IF NOT EXISTS cug_director_confirmation (
    id              BIGSERIAL    PRIMARY KEY,
    director_name   TEXT,
    signature_date  DATE,
    signature_data  TEXT,          -- base64 data-URL of the drawn signature
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Add signature_data if table already existed without it
ALTER TABLE cug_director_confirmation
    ADD COLUMN IF NOT EXISTS signature_data TEXT;

-- Add updated_at if table already existed without it
ALTER TABLE cug_director_confirmation
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE OR REPLACE FUNCTION _cug_confirmation_set_updated()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_cug_confirmation_updated ON cug_director_confirmation;
CREATE TRIGGER trg_cug_confirmation_updated
    BEFORE UPDATE ON cug_director_confirmation
    FOR EACH ROW EXECUTE FUNCTION _cug_confirmation_set_updated();


-- ── 3. Row Level Security ─────────────────────────────────────────────────────
ALTER TABLE cug_corrections            ENABLE ROW LEVEL SECURITY;
ALTER TABLE cug_director_confirmation  ENABLE ROW LEVEL SECURITY;

-- Anon can SELECT (page-load reads)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'cug_corrections' AND policyname = 'anon read corrections'
  ) THEN
    CREATE POLICY "anon read corrections"
        ON cug_corrections FOR SELECT USING (TRUE);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'cug_director_confirmation' AND policyname = 'anon read confirmation'
  ) THEN
    CREATE POLICY "anon read confirmation"
        ON cug_director_confirmation FOR SELECT USING (TRUE);
  END IF;
END $$;

-- Service role (Django backend) has full access
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'cug_corrections' AND policyname = 'service all corrections'
  ) THEN
    CREATE POLICY "service all corrections"
        ON cug_corrections FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'cug_director_confirmation' AND policyname = 'service all confirmation'
  ) THEN
    CREATE POLICY "service all confirmation"
        ON cug_director_confirmation FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;

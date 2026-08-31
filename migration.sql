-- Phase 1: Expand tariff_events with intelligence fields
ALTER TABLE tariff_events
  ADD COLUMN IF NOT EXISTS winners JSONB,
  ADD COLUMN IF NOT EXISTS losers JSONB,
  ADD COLUMN IF NOT EXISTS affected_companies JSONB,
  ADD COLUMN IF NOT EXISTS inflation_implications TEXT,
  ADD COLUMN IF NOT EXISTS supply_chain_implications TEXT,
  ADD COLUMN IF NOT EXISTS stocks_to_watch JSONB,
  ADD COLUMN IF NOT EXISTS etfs_affected JSONB,
  ADD COLUMN IF NOT EXISTS commodities_affected JSONB;

-- Phase 2: Companies table
CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  sector TEXT NOT NULL,
  description TEXT,
  headquarters_country TEXT DEFAULT 'United States',
  tariff_exposure_score INTEGER CHECK (tariff_exposure_score BETWEEN 0 AND 100),
  china_exposure_score INTEGER CHECK (china_exposure_score BETWEEN 0 AND 100),
  supply_chain_risk_score INTEGER CHECK (supply_chain_risk_score BETWEEN 0 AND 100),
  import_dependency_score INTEGER CHECK (import_dependency_score BETWEEN 0 AND 100),
  score_rationale TEXT,
  key_risks TEXT[],
  key_opportunities TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

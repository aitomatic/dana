-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Vector store table
CREATE TABLE IF NOT EXISTS vector_store (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    embedding vector NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Time series store table
CREATE TABLE IF NOT EXISTS time_series_store (
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('time_series_store', 'timestamp');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_time_series_key ON time_series_store (key);
CREATE INDEX IF NOT EXISTS idx_time_series_timestamp ON time_series_store (timestamp DESC);

-- Relational store tables
CREATE TABLE IF NOT EXISTS process_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS process_parameters (
    id TEXT PRIMARY KEY,
    process_id TEXT NOT NULL REFERENCES process_configs(id),
    name TEXT NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_process_type ON process_configs (type);
CREATE INDEX IF NOT EXISTS idx_process_status ON process_configs (status);
CREATE INDEX IF NOT EXISTS idx_parameters_process ON process_parameters (process_id);

-- Create update triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_vector_store_updated_at
    BEFORE UPDATE ON vector_store
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_process_configs_updated_at
    BEFORE UPDATE ON process_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_process_parameters_updated_at
    BEFORE UPDATE ON process_parameters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at(); 
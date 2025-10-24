-- Supabase Database Schema for QuFLX Trading Data
-- Organization: StanWeb
-- Project: QuFLX

-- =====================================================
-- ASSETS TABLE
-- =====================================================
-- Stores information about trading assets/pairs
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,        -- e.g., 'EURUSD_otc'
    base_currency VARCHAR(10) NOT NULL,        -- e.g., 'EUR'
    quote_currency VARCHAR(10) NOT NULL,       -- e.g., 'USD'
    asset_type VARCHAR(20) DEFAULT 'forex',    -- forex, crypto, etc.
    display_name VARCHAR(50),                  -- Human readable name
    is_active BOOLEAN DEFAULT true,            -- Active trading pair
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CANDLES TABLE (PARTITIONED)
-- =====================================================
-- Stores OHLC candle data with partitioning by timeframe
CREATE TABLE IF NOT EXISTS candles (
    id BIGSERIAL,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timeframe VARCHAR(5) NOT NULL,              -- '1m', '5m', '15m', '1H', '4H'
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(20,10) NOT NULL,
    high DECIMAL(20,10) NOT NULL,
    low DECIMAL(20,10) NOT NULL,
    close DECIMAL(20,10) NOT NULL,
    volume BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (asset_id, timeframe, timestamp)
) PARTITION BY LIST (timeframe);

-- Create partitions for each timeframe
CREATE TABLE IF NOT EXISTS candles_1m PARTITION OF candles FOR VALUES IN ('1m');
CREATE TABLE IF NOT EXISTS candles_5m PARTITION OF candles FOR VALUES IN ('5m');
CREATE TABLE IF NOT EXISTS candles_15m PARTITION OF candles FOR VALUES IN ('15m');
CREATE TABLE IF NOT EXISTS candles_1h PARTITION OF candles FOR VALUES IN ('1H');
CREATE TABLE IF NOT EXISTS candles_4h PARTITION OF candles FOR VALUES IN ('4H');

-- =====================================================
-- INGESTION LOGS TABLE
-- =====================================================
-- Tracks CSV file ingestion operations
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id SERIAL PRIMARY KEY,
    asset_symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    file_path TEXT NOT NULL,
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',      -- pending, processing, completed, failed, partial
    error_message TEXT,
    processing_time_seconds DECIMAL(10,2),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_candles_asset_timeframe_timestamp
    ON candles (asset_id, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_timestamp
    ON candles (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_asset_timestamp
    ON candles (asset_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_asset_timeframe
    ON ingestion_logs (asset_symbol, timeframe);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_processed_at
    ON ingestion_logs (processed_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_status
    ON ingestion_logs (status);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================
-- Enable RLS
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE candles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_logs ENABLE ROW LEVEL SECURITY;

-- Policies for assets table
CREATE POLICY "Assets are viewable by everyone" ON assets
    FOR SELECT USING (true);

CREATE POLICY "Assets are insertable by authenticated users" ON assets
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Policies for candles table
CREATE POLICY "Candles are viewable by everyone" ON candles
    FOR SELECT USING (true);

CREATE POLICY "Candles are insertable by authenticated users" ON candles
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Policies for ingestion_logs table
CREATE POLICY "Ingestion logs are viewable by authenticated users" ON ingestion_logs
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Ingestion logs are insertable by authenticated users" ON ingestion_logs
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
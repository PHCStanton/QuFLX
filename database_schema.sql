-- =====================================================
-- HISTORICAL_TICKS TABLE
-- =====================================================
-- Stores individual tick data for high-resolution analysis
CREATE TABLE IF NOT EXISTS historical_ticks (
    id BIGSERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,        -- e.g., 'EURUSD_otc'
    price DECIMAL(20,10) NOT NULL,    -- Tick price
    timestamp BIGINT NOT NULL,        -- Unix timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR HISTORICAL_TICKS
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_historical_ticks_pair_timestamp 
    ON historical_ticks (pair, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_ticks_timestamp 
    ON historical_ticks (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_ticks_pair 
    ON historical_ticks (pair);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES FOR HISTORICAL_TICKS
-- =====================================================
ALTER TABLE historical_ticks ENABLE ROW LEVEL SECURITY;

-- Policies for historical_ticks table
CREATE POLICY "Historical ticks are viewable by everyone" ON historical_ticks
    FOR SELECT USING (true);

CREATE POLICY "Historical ticks are insertable by authenticated users" ON historical_ticks
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- =====================================================
-- EXISTING TABLES (from original schema)
-- =====================================================

-- Add any existing tables from your original schema here
-- For example, if you had a candles table:

-- CREATE TABLE IF NOT EXISTS candles (
--     id BIGSERIAL PRIMARY KEY,
--     pair VARCHAR(20) NOT NULL,
--     timeframe VARCHAR(10) NOT NULL,
--     open_price DECIMAL(20,10) NOT NULL,
--     high_price DECIMAL(20,10) NOT NULL,
--     low_price DECIMAL(20,10) NOT NULL,
--     close_price DECIMAL(20,10) NOT NULL,
--     volume BIGINT DEFAULT 0,
--     timestamp BIGINT NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- =====================================================
-- FUNCTIONS AND TRIGGERS (if needed)
-- =====================================================

-- Function to update modified timestamp
-- CREATE OR REPLACE FUNCTION update_modified_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = NOW();
--     RETURN NEW;
-- END;
-- $$ language 'plpgsql';

-- =====================================================
-- VIEWS (if needed)
-- =====================================================

-- View for latest tick data per pair
-- CREATE OR REPLACE VIEW latest_ticks AS
-- SELECT DISTINCT ON (pair) 
--     pair,
--     price,
--     timestamp,
--     created_at
-- FROM historical_ticks
-- ORDER BY pair, timestamp DESC;

-- =====================================================
-- SAMPLE DATA (for testing)
-- =====================================================

-- Insert sample tick data for testing
-- INSERT INTO historical_ticks (pair, price, timestamp) VALUES
-- ('EURUSD_otc', 1.0823, EXTRACT(EPOCH FROM NOW())::BIGINT),
-- ('GBPUSD_otc', 1.2745, EXTRACT(EPOCH FROM NOW())::BIGINT),
-- ('EURUSD_otc', 1.0824, EXTRACT(EPOCH FROM NOW() + INTERVAL '1 second')::BIGINT);

-- =====================================================
-- PERFORMANCE OPTIMIZATION
-- =====================================================

-- Set up table partitioning if needed for large datasets
-- This would be implemented based on your data volume requirements

-- Example partitioning by date (PostgreSQL 10+)
-- CREATE TABLE historical_ticks_y2024m01 PARTITION OF historical_ticks
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- =====================================================
-- MAINTENANCE PROCEDURES
-- =====================================================

-- Procedure to clean up old data (older than 1 year)
-- CREATE OR REPLACE FUNCTION cleanup_old_ticks()
-- RETURNS void AS $$
-- BEGIN
--     DELETE FROM historical_ticks 
--     WHERE created_at < NOW() - INTERVAL '1 year';
-- END;
-- $$ LANGUAGE plpgsql;

-- =====================================================
-- MONITORING QUERIES
-- =====================================================

-- Query to check table size
-- SELECT 
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
-- FROM pg_tables 
-- WHERE tablename = 'historical_ticks';

-- Query to check index usage
-- SELECT 
--     indexrelname,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes 
-- WHERE schemaname = 'public' AND tablename = 'historical_ticks';
# Supabase Configuration for QuFLX Project
# Organization: StanWeb
# Project: QuFLX

SUPABASE_URL = "https://gcllapblikrbmlsygnbp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjbGxhcGJsaWtyYm1sc3lnbmJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk3MzM4MjksImV4cCI6MjA3NTMwOTgyOX0.3K20InV68I7dEd2pI7kxVVJyq6S1bodhSjyCHsYuls8"
SUPABASE_SERVICE_ROLE_KEY = "sb_secret_nGUifqjYMjjgtVQDWPuHcg_am6Q1h-j"  # For admin operations

# Database connection settings
DB_HOST = "db.gcllapblikrbmlsygnbp.supabase.co"
DB_PORT = 5432
DB_NAME = "postgres"

# Batch processing settings
BATCH_SIZE = 1000
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
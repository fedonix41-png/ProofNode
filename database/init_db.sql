-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for users
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram ID
    username VARCHAR(100),
    is_premium BOOLEAN DEFAULT FALSE,
    premium_expires_at TIMESTAMP WITH TIME ZONE,
    referral_code VARCHAR(20) UNIQUE,
    referred_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for B2B trader profiles (VIP signal channel admins)
CREATE TABLE IF NOT EXISTS trader_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    public_slug VARCHAR(50) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Wallets attached to trader profiles for Proof-of-Trade
CREATE TABLE IF NOT EXISTS trader_wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trader_profile_id UUID NOT NULL REFERENCES trader_profiles(id) ON DELETE CASCADE,
    blockchain VARCHAR(10) NOT NULL, -- 'TON', 'BASE', 'SOL'
    address VARCHAR(256) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blockchain, address)
);

-- Subscription tariffs offered by traders
CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trader_profile_id UUID NOT NULL REFERENCES trader_profiles(id) ON DELETE CASCADE,
    duration_days INT NOT NULL,
    price_stars INT, -- Price in Telegram Stars
    price_crypto NUMERIC(20, 9), -- Price in crypto (TON/USDT)
    currency VARCHAR(10) DEFAULT 'TON'
);

-- User subscriptions to trader channels
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trader_profile_id UUID NOT NULL REFERENCES trader_profiles(id) ON DELETE CASCADE,
    tariff_id UUID REFERENCES tariffs(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'EXPIRED', 'CANCELLED'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    invite_link VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Monitored wallets for the B2C smart money tracker
CREATE TABLE IF NOT EXISTS monitored_wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blockchain VARCHAR(10) NOT NULL, -- 'TON', 'BASE', 'SOL'
    address VARCHAR(256) NOT NULL,
    label VARCHAR(100),
    push_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, blockchain, address)
);

-- Timeseries Table: blockchain wallet transactions (swaps/transfers)
CREATE TABLE IF NOT EXISTS wallet_transactions (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    tx_hash VARCHAR(128) NOT NULL,
    trace_id VARCHAR(128), -- For TON logical trace correlation
    logical_time BIGINT, -- For TON lt sequence sorting
    wallet_address VARCHAR(256) NOT NULL,
    blockchain VARCHAR(10) NOT NULL, -- 'TON', 'BASE', 'SOL'
    dex_name VARCHAR(50), -- e.g., 'Ston.fi', 'DeDust', 'Jupiter', 'Uniswap'
    token_in_address VARCHAR(256),
    token_out_address VARCHAR(256),
    amount_in NUMERIC(40, 18),
    amount_out NUMERIC(40, 18),
    usd_value NUMERIC(15, 2),
    tx_type VARCHAR(10) NOT NULL, -- 'BUY', 'SELL', 'TRANSFER'
    PRIMARY KEY (time, tx_hash, wallet_address)
);

-- Convert transactions table to hypertable partitioned by 7 days
SELECT create_hypertable('wallet_transactions', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

-- Configure TimescaleDB compression for transactions (records older than 14 days)
ALTER TABLE wallet_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'wallet_address, blockchain',
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('wallet_transactions', INTERVAL '14 days', if_not_exists => TRUE);

-- Configure TimescaleDB retention policy (delete raw logs older than 90 days)
SELECT add_retention_policy('wallet_transactions', INTERVAL '90 days', if_not_exists => TRUE);

-- Timeseries Table: Trader Profit & Loss history (for ROI charting)
CREATE TABLE IF NOT EXISTS trader_pnl_history (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    trader_profile_id UUID NOT NULL,
    daily_roi NUMERIC(8, 4), -- Daily ROI in %
    cumulative_roi NUMERIC(12, 4), -- Cumulative ROI in %
    winrate NUMERIC(5, 2),
    drawdown NUMERIC(5, 2),
    PRIMARY KEY (time, trader_profile_id)
);

-- Convert PnL history table to hypertable partitioned by 30 days
SELECT create_hypertable('trader_pnl_history', 'time', chunk_time_interval => INTERVAL '30 days', if_not_exists => TRUE);

-- Table for storing server-side SSS Share 2
CREATE TABLE IF NOT EXISTS user_sss_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blockchain VARCHAR(10) NOT NULL, -- 'TON', 'BASE', 'SOL'
    address VARCHAR(256) NOT NULL,
    server_share TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, blockchain, address)
);

-- Table for user proxy wallets (automated cloud copy-trading)
CREATE TABLE IF NOT EXISTS user_proxy_wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blockchain VARCHAR(10) NOT NULL, -- 'TON', 'BASE', 'SOL'
    address VARCHAR(256) NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    balance NUMERIC(40, 18) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, blockchain)
);

-- Copy-trading configurations per trader subscription
CREATE TABLE IF NOT EXISTS copy_trade_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    copy_mode VARCHAR(20) NOT NULL, -- '1-CLICK', 'AUTOMATED'
    proxy_wallet_id UUID REFERENCES user_proxy_wallets(id) ON DELETE SET NULL,
    max_allocation_per_trade NUMERIC(40, 18) NOT NULL,
    slippage_bps INT NOT NULL DEFAULT 100, -- e.g. 100 bps = 1%
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (subscription_id)
);

-- Table for tracking pending 1-Click Copy-Trading signals
CREATE TABLE IF NOT EXISTS pending_copy_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trader_tx_hash VARCHAR(128) NOT NULL,
    blockchain VARCHAR(10) NOT NULL,
    token_in_address VARCHAR(256) NOT NULL,
    token_out_address VARCHAR(256) NOT NULL,
    amount_in NUMERIC(40, 18) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'EXECUTED', 'EXPIRED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for recording completed copy-trade transactions
CREATE TABLE IF NOT EXISTS copy_trade_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trader_tx_hash VARCHAR(128) NOT NULL,
    copy_tx_hash VARCHAR(128),
    blockchain VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED'
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


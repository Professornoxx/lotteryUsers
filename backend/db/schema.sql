-- ============================================================
-- Lottery Users Dashboard - PostgreSQL / Supabase Schema
-- ============================================================

-- 1. Core user profile
CREATE TABLE IF NOT EXISTS users (
    user_id           BIGINT PRIMARY KEY,
    username          VARCHAR(100),
    gender            SMALLINT,
    phone             VARCHAR(20),
    email             VARCHAR(200),
    birth_date        TIMESTAMP,
    city              VARCHAR(100),
    register_ip       VARCHAR(50),
    user_status       SMALLINT DEFAULT 0,
    is_test           SMALLINT DEFAULT 0,
    app_version       VARCHAR(50),
    reg_version       VARCHAR(50),
    reg_source        VARCHAR(50),
    reg_channel       VARCHAR(100),
    package_id        INTEGER,
    mark              VARCHAR(500),
    tag               VARCHAR(200),
    create_time       TIMESTAMP,
    update_time       TIMESTAMP
);

-- 2. Financial data
CREATE TABLE IF NOT EXISTS user_financials (
    user_id            BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    balance            NUMERIC(18,2) DEFAULT 0,
    user_balance       NUMERIC(18,2) DEFAULT 0,
    total_deposits     NUMERIC(18,2) DEFAULT 0,
    total_withdrawals  NUMERIC(18,2) DEFAULT 0,
    frozen_amount      NUMERIC(18,2) DEFAULT 0,
    withdraw_limit     NUMERIC(18,2) DEFAULT 0,
    recharge_count     INTEGER DEFAULT 0
);

-- 3. Agent / referral hierarchy
CREATE TABLE IF NOT EXISTS user_agents (
    user_id          BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    agent_status     SMALLINT,
    agent_user_id    BIGINT,
    parent_user_id   BIGINT,
    direct_parent    BIGINT,
    agent_level1     BIGINT,
    agent_level2     BIGINT,
    agent_level3     BIGINT,
    agent_level4     BIGINT,
    agent_level      SMALLINT,
    inviter_user_id  BIGINT,
    member_level     SMALLINT DEFAULT 0
);

-- 4. Device tracking
CREATE TABLE IF NOT EXISTS user_devices (
    user_id             BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    register_device     VARCHAR(200),
    login_device        VARCHAR(200),
    last_login_device   VARCHAR(200),
    device_id           VARCHAR(200),
    push_token          VARCHAR(500),
    last_active_time    TIMESTAMP
);

-- 5. IM / Chat
CREATE TABLE IF NOT EXISTS user_im (
    user_id          BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    im_user_id       VARCHAR(100),
    im_user_status   VARCHAR(10),
    im_customer      VARCHAR(100),
    group_name       VARCHAR(100),
    adjust_adid      VARCHAR(200)
);

-- 6. CRM follow-up
CREATE TABLE IF NOT EXISTS user_followup (
    user_id            BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    flow_up_time       TIMESTAMP,
    next_flow_up_time  TIMESTAMP
);

-- 7. Admin users
CREATE TABLE IF NOT EXISTS admin_users (
    admin_id      SERIAL PRIMARY KEY,
    username      VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role          VARCHAR(50) DEFAULT 'admin',
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_users_city        ON users(city);
CREATE INDEX IF NOT EXISTS idx_users_status      ON users(user_status);
CREATE INDEX IF NOT EXISTS idx_users_channel     ON users(reg_channel);
CREATE INDEX IF NOT EXISTS idx_users_source      ON users(reg_source);
CREATE INDEX IF NOT EXISTS idx_users_create_time ON users(create_time);
CREATE INDEX IF NOT EXISTS idx_users_phone       ON users(phone);
CREATE INDEX IF NOT EXISTS idx_fin_deposits      ON user_financials(total_deposits);
CREATE INDEX IF NOT EXISTS idx_fin_balance       ON user_financials(balance);
CREATE INDEX IF NOT EXISTS idx_agent_status      ON user_agents(agent_status);
CREATE INDEX IF NOT EXISTS idx_agent_parent      ON user_agents(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_dev_active        ON user_devices(last_active_time);

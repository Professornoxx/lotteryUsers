-- ============================================================
-- Lottery Users Dashboard - Oracle Database Schema
-- ============================================================

-- 1. Core user profile
CREATE TABLE USERS (
    user_id           NUMBER PRIMARY KEY,
    username          VARCHAR2(100),
    gender            NUMBER(1),          -- 0=male, 1=female
    phone             VARCHAR2(20),
    email             VARCHAR2(200),
    birth_date        DATE,
    city              VARCHAR2(100),
    register_ip       VARCHAR2(50),
    user_status       NUMBER(1) DEFAULT 0, -- 0=active, 1=banned
    is_test           NUMBER(1) DEFAULT 0, -- 0=real, 1=test
    app_version       VARCHAR2(50),
    reg_version       VARCHAR2(50),
    reg_source        VARCHAR2(50),        -- Android, h5
    reg_channel       VARCHAR2(100),       -- Organic, AppShare, Promotion
    package_id        NUMBER,
    mark              VARCHAR2(500),
    tag               VARCHAR2(200),
    create_time       TIMESTAMP,
    update_time       TIMESTAMP
);

-- 2. Financial data
CREATE TABLE USER_FINANCIALS (
    user_id            NUMBER PRIMARY KEY,
    balance            NUMBER(18,2) DEFAULT 0,
    user_balance       NUMBER(18,2) DEFAULT 0,
    total_deposits     NUMBER(18,2) DEFAULT 0,
    total_withdrawals  NUMBER(18,2) DEFAULT 0,
    frozen_amount      NUMBER(18,2) DEFAULT 0,
    withdraw_limit     NUMBER(18,2) DEFAULT 0,
    recharge_count     NUMBER DEFAULT 0,
    CONSTRAINT fk_fin_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- 3. Agent / referral hierarchy
CREATE TABLE USER_AGENTS (
    user_id          NUMBER PRIMARY KEY,
    agent_status     NUMBER(1),   -- 0=not applied,1=pending,2=rejected,3=approved
    agent_user_id    NUMBER,
    parent_user_id   NUMBER,
    direct_parent    NUMBER,
    agent_level1     NUMBER,
    agent_level2     NUMBER,
    agent_level3     NUMBER,
    agent_level4     NUMBER,
    agent_level      NUMBER,
    inviter_user_id  NUMBER,
    member_level     NUMBER DEFAULT 0,
    CONSTRAINT fk_agent_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- 4. Device tracking
CREATE TABLE USER_DEVICES (
    user_id             NUMBER PRIMARY KEY,
    register_device     VARCHAR2(200),
    login_device        VARCHAR2(200),
    last_login_device   VARCHAR2(200),
    device_id           VARCHAR2(200),
    push_token          VARCHAR2(500),
    last_active_time    TIMESTAMP,
    CONSTRAINT fk_dev_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- 5. IM / Chat integration
CREATE TABLE USER_IM (
    user_id          NUMBER PRIMARY KEY,
    im_user_id       VARCHAR2(100),
    im_user_status   VARCHAR2(10),
    im_customer      VARCHAR2(100),
    group_name       VARCHAR2(100),
    adjust_adid      VARCHAR2(200),
    CONSTRAINT fk_im_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- 6. CRM follow-up scheduling
CREATE TABLE USER_FOLLOWUP (
    user_id            NUMBER PRIMARY KEY,
    flow_up_time       TIMESTAMP,
    next_flow_up_time  TIMESTAMP,
    CONSTRAINT fk_fu_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- 7. Dashboard admin users
CREATE TABLE ADMIN_USERS (
    admin_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      VARCHAR2(100) UNIQUE NOT NULL,
    password_hash VARCHAR2(200) NOT NULL,
    role          VARCHAR2(50) DEFAULT 'admin',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX idx_users_city        ON USERS(city);
CREATE INDEX idx_users_status      ON USERS(user_status);
CREATE INDEX idx_users_channel     ON USERS(reg_channel);
CREATE INDEX idx_users_source      ON USERS(reg_source);
CREATE INDEX idx_users_create_time ON USERS(create_time);
CREATE INDEX idx_users_phone       ON USERS(phone);
CREATE INDEX idx_fin_deposits      ON USER_FINANCIALS(total_deposits);
CREATE INDEX idx_fin_balance       ON USER_FINANCIALS(balance);
CREATE INDEX idx_agent_status      ON USER_AGENTS(agent_status);
CREATE INDEX idx_agent_parent      ON USER_AGENTS(parent_user_id);
CREATE INDEX idx_dev_active        ON USER_DEVICES(last_active_time);

-- ============================================================
-- Default admin user (password: Admin@123 - change immediately)
-- ============================================================
INSERT INTO ADMIN_USERS (username, password_hash, role)
VALUES ('admin', '$2b$12$placeholder_change_this', 'superadmin');

COMMIT;

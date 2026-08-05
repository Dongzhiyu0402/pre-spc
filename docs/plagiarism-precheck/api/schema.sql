-- =============================================================
-- 预查重项目 数据库 Schema v1.0
-- 依据：Spec-预查重项目-v1.0.md §6（唯一依据）
-- 目标：PostgreSQL 16
-- 约定：
--   * 表名蛇形复数
--   * 每表必有 id (BIGSERIAL)、created_at、updated_at
--   * 枚举值用 TEXT + CHECK 约束（MVP 轻量，避免 ALTER TYPE 迁移负担）
--   * 金额/比例类字段用 NUMERIC，禁用 FLOAT（防沉默逻辑错误：浮点精度）
--   * 软删除：暂无业务需要，全部硬删除（MVP 收敛）
-- =============================================================

BEGIN;

-- -------------------------------------------------------------
-- 1. users 用户
-- -------------------------------------------------------------
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT        NOT NULL,
    password_hash TEXT        NOT NULL,
    nickname      TEXT        NOT NULL,
    role          TEXT        NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user', 'admin')),
    free_quota    INTEGER     NOT NULL DEFAULT 5
                  CHECK (free_quota >= 0),
    points        INTEGER     NOT NULL DEFAULT 0
                  CHECK (points >= 0),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uk_users_email ON users (lower(email));

-- -------------------------------------------------------------
-- 2. plans 查重方案（可配置，新增平台无需发版 -> AC-11）
-- -------------------------------------------------------------
CREATE TABLE plans (
    id          BIGSERIAL PRIMARY KEY,
    code        TEXT        NOT NULL,
    name        TEXT        NOT NULL,
    type        TEXT        NOT NULL
                CHECK (type IN ('engine', 'api')),
    params_json JSONB       NOT NULL DEFAULT '{}'::jsonb,
    enabled     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uk_plans_code ON plans (code);

-- -------------------------------------------------------------
-- 3. check_tasks 查重任务
-- -------------------------------------------------------------
CREATE TABLE check_tasks (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT      NOT NULL REFERENCES users (id),
    plan_code      TEXT        NOT NULL REFERENCES plans (code),
    file_name      TEXT        NOT NULL,
    file_size      BIGINT      NOT NULL DEFAULT 0
                   CHECK (file_size >= 0),
    word_count     INTEGER     NOT NULL DEFAULT 0
                   CHECK (word_count >= 0 AND word_count <= 100000),
    status         TEXT        NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'processing', 'succeeded', 'failed')),
    engine_version TEXT        NOT NULL,
    error_message  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_check_tasks_user ON check_tasks (user_id, created_at DESC);
CREATE INDEX idx_check_tasks_status ON check_tasks (status);

-- -------------------------------------------------------------
-- 4. check_results 查重结果（1:1 with check_tasks）
-- -------------------------------------------------------------
CREATE TABLE check_results (
    id            BIGSERIAL PRIMARY KEY,
    task_id       BIGINT      NOT NULL UNIQUE REFERENCES check_tasks (id),
    raw_score     NUMERIC(5,2) NOT NULL CHECK (raw_score >= 0 AND raw_score <= 100),
    est_median    NUMERIC(5,2) NOT NULL CHECK (est_median >= 0 AND est_median <= 100),
    est_low       NUMERIC(5,2) NOT NULL CHECK (est_low >= 0 AND est_low <= 100),
    est_high      NUMERIC(5,2) NOT NULL CHECK (est_high >= 0 AND est_high <= 100),
    confidence    NUMERIC(5,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    segments_json JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- 区间一致性：low <= median <= high（防沉默逻辑错误）
    CONSTRAINT chk_check_results_interval
        CHECK (est_low <= est_median AND est_median <= est_high)
);

CREATE INDEX idx_check_results_task ON check_results (task_id);

-- -------------------------------------------------------------
-- 5. check_segments 命中片段（报告高亮）
-- -------------------------------------------------------------
CREATE TABLE check_segments (
    id             BIGSERIAL PRIMARY KEY,
    result_id      BIGINT      NOT NULL REFERENCES check_results (id),
    start_offset   INTEGER     NOT NULL CHECK (start_offset >= 0),
    end_offset     INTEGER     NOT NULL,
    highlight_type TEXT        NOT NULL
                   CHECK (highlight_type IN ('high', 'mid', 'cite')),
    matched_source TEXT        NOT NULL DEFAULT '',
    similarity     NUMERIC(5,2) NOT NULL CHECK (similarity >= 0 AND similarity <= 100),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- 偏移一致性：end > start
    CONSTRAINT chk_check_segments_offset CHECK (end_offset > start_offset)
);

CREATE INDEX idx_check_segments_result ON check_segments (result_id);

-- -------------------------------------------------------------
-- 6. calibration_samples 校准样本（用户回传真实报告 -> AC-14）
-- -------------------------------------------------------------
CREATE TABLE calibration_samples (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users (id),
    task_id     BIGINT      NOT NULL REFERENCES check_tasks (id),
    platform    TEXT        NOT NULL
                CHECK (platform IN ('cnki', 'vip', 'wanfang')),
    real_rate   NUMERIC(5,2) NOT NULL CHECK (real_rate >= 0 AND real_rate <= 100),
    report_file TEXT        NOT NULL,
    validated   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_calibration_samples_platform ON calibration_samples (platform, validated);
CREATE INDEX idx_calibration_samples_user ON calibration_samples (user_id);

-- -------------------------------------------------------------
-- 7. calibration_models 校准模型（按 平台+论文类型 分桶 -> 不混训）
-- -------------------------------------------------------------
CREATE TABLE calibration_models (
    id            BIGSERIAL PRIMARY KEY,
    platform      TEXT        NOT NULL
                  CHECK (platform IN ('cnki', 'vip', 'wanfang')),
    paper_type    TEXT        NOT NULL DEFAULT 'undergrad'
                  CHECK (paper_type IN ('undergrad', 'postgrad', 'journal')),
    sample_count  INTEGER     NOT NULL DEFAULT 0 CHECK (sample_count >= 0),
    model_version TEXT        NOT NULL,
    mae           NUMERIC(5,2),
    params_json   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    trained_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uk_calibration_models_bucket UNIQUE (platform, paper_type)
);

-- -------------------------------------------------------------
-- 8. point_transactions 积分流水（防滥用 -> AC-13）
-- -------------------------------------------------------------
CREATE TABLE point_transactions (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users (id),
    amount     INTEGER     NOT NULL CHECK (amount <> 0),
    type       TEXT        NOT NULL
               CHECK (type IN ('grant', 'consume', 'refund', 'calibration_reward')),
    reason     TEXT        NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_point_transactions_user ON point_transactions (user_id, created_at DESC);

-- -------------------------------------------------------------
-- 触发器：updated_at 自动更新（所有带 updated_at 的表）
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['users', 'plans', 'check_tasks', 'check_results', 'calibration_samples', 'calibration_models']
    LOOP
        EXECUTE format('CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_updated_at();', t, t);
    END LOOP;
END;
$$;

COMMIT;

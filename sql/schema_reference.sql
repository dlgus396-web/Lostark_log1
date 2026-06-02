-- Supabase DB 테이블 스키마 참고용 (예시)

-- supported_classes
CREATE TABLE supported_classes (
    class_name TEXT PRIMARY KEY,
    attack_type TEXT,
    is_supported BOOLEAN,
    created_at TIMESTAMPTZ
);

-- bosses
CREATE TABLE bosses (
    id BIGSERIAL PRIMARY KEY,
    boss_code TEXT,
    raid_name TEXT,
    gate_no INTEGER,
    difficulty TEXT,
    boss_display_name TEXT,
    created_at TIMESTAMPTZ
);

-- score_rules
CREATE TABLE score_rules (
    id BIGSERIAL PRIMARY KEY,
    class_name TEXT,
    metric_name TEXT,
    weight NUMERIC,
    version TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ
);

-- scoring_baselines
CREATE TABLE scoring_baselines (
    id BIGSERIAL PRIMARY KEY,
    class_name TEXT,
    boss_id BIGINT,
    metric_name TEXT,
    baseline_median NUMERIC,
    baseline_q3 NUMERIC,
    baseline_ceiling NUMERIC,
    baseline_best NUMERIC,
    source_type TEXT,
    source_url TEXT,
    source_note TEXT,
    patch_name TEXT,
    ilvl_min INTEGER,
    ilvl_max INTEGER,
    version TEXT
);

-- combat_records
CREATE TABLE combat_records (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    class_name TEXT,
    boss_id BIGINT,
    boss_name_raw TEXT,
    screenshot_url TEXT,
    ocr_raw_text TEXT,
    ocr_status TEXT,
    final_score NUMERIC,
    key_action_cpm NUMERIC,
    back_attack_rate NUMERIC,
    head_attack_rate NUMERIC,
    score_version TEXT,
    video_url TEXT,
    created_at TIMESTAMPTZ
);

-- reports
CREATE TABLE reports (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT,
    reporter_user_id UUID,
    report_reason TEXT,
    created_at TIMESTAMPTZ
);

-- profiles
CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    discord_user_id TEXT,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ
);

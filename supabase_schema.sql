-- Telegram Agent Manager Supabase Schema
-- 하나의 계정이 여러 그룹에서 서로 다른 페르소나와 역할을 수행하는 시스템

-- 1. 계정 테이블 (기본)
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    api_id INTEGER NOT NULL,
    api_hash VARCHAR(32) NOT NULL,
    session_string TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 그룹/채팅방 테이블
CREATE TABLE chat_groups (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL, -- 텔레그램 채팅 ID
    chat_title VARCHAR(255),
    chat_type VARCHAR(50), -- 'group', 'supergroup', 'channel'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 에이전트 역할 테이블 (핵심)
CREATE TABLE agent_roles (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    chat_group_id INTEGER REFERENCES chat_groups(id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL, -- 'Chatter', 'Moderator', 'Admin'
    persona TEXT NOT NULL, -- 해당 역할의 페르소나
    is_active BOOLEAN DEFAULT TRUE,
    openai_api_key VARCHAR(100), -- 개별 역할별 OpenAI 키
    response_delay_ms INTEGER DEFAULT 0, -- 응답 지연 시간
    max_response_length INTEGER DEFAULT 500, -- 최대 응답 길이
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 한 계정이 한 그룹에서 하나의 역할만 가질 수 있음
    UNIQUE(account_id, chat_group_id)
);

-- 4. 메시지 로그 테이블
CREATE TABLE message_logs (
    id SERIAL PRIMARY KEY,
    agent_role_id INTEGER REFERENCES agent_roles(id) ON DELETE CASCADE,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    response_text TEXT,
    response_time_ms INTEGER,
    role_used VARCHAR(50), -- 실제 사용된 역할
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 인증 세션 테이블 (2FA 및 인증 상태 관리)
CREATE TABLE auth_sessions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    phone_code_hash VARCHAR(255), -- 2FA 코드 해시
    is_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 인덱스 생성 (성능 최적화)
CREATE INDEX idx_accounts_phone ON accounts(phone_number);
CREATE INDEX idx_accounts_active ON accounts(is_active);
CREATE INDEX idx_agent_roles_account ON agent_roles(account_id);
CREATE INDEX idx_agent_roles_chat ON agent_roles(chat_group_id);
CREATE INDEX idx_agent_roles_active ON agent_roles(is_active);
CREATE INDEX idx_message_logs_role ON message_logs(agent_role_id);
CREATE INDEX idx_message_logs_chat ON message_logs(chat_id);
CREATE INDEX idx_message_logs_created ON message_logs(created_at);
CREATE INDEX idx_auth_sessions_token ON auth_sessions(session_token);
CREATE INDEX idx_auth_sessions_account ON auth_sessions(account_id);

-- 7. RLS (Row Level Security) 설정
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY;

-- 8. 기본 정책 (모든 사용자가 읽기 가능, 인증된 사용자만 쓰기 가능)
CREATE POLICY "Enable read access for all users" ON accounts FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON accounts FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON accounts FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON chat_groups FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON chat_groups FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON chat_groups FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON agent_roles FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON agent_roles FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON agent_roles FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON message_logs FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON message_logs FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable read access for all users" ON auth_sessions FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON auth_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON auth_sessions FOR UPDATE USING (true);

-- 9. 함수 및 트리거 (자동 업데이트 시간)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_groups_updated_at BEFORE UPDATE ON chat_groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_roles_updated_at BEFORE UPDATE ON agent_roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. 뷰 생성 (자주 사용되는 쿼리)
CREATE VIEW account_roles_view AS
SELECT 
    a.id as account_id,
    a.phone_number,
    a.username,
    a.first_name,
    a.last_name,
    a.is_active as account_active,
    ar.id as role_id,
    ar.role_name,
    ar.persona,
    ar.is_active as role_active,
    cg.chat_id,
    cg.chat_title,
    cg.chat_type
FROM accounts a
LEFT JOIN agent_roles ar ON a.id = ar.account_id
LEFT JOIN chat_groups cg ON ar.chat_group_id = cg.id
WHERE a.is_active = true;

-- 11. 샘플 데이터 (테스트용)
INSERT INTO accounts (phone_number, api_id, api_hash, session_string, user_id, username, first_name, last_name, is_verified, is_active) VALUES
('+1234567890', 12345, 'test_api_hash_1234567890abcdef', 'test_session_string_1234567890abcdef', 123456789, 'test_bot', 'Test', 'Bot', true, true);

INSERT INTO chat_groups (chat_id, chat_title, chat_type, is_active) VALUES
(-1001234567890, 'Test Developer Group', 'supergroup', true),
(-1009876543210, 'Test Game Group', 'supergroup', true),
(-1005556667777, 'Test Business Group', 'supergroup', true);

INSERT INTO agent_roles (account_id, chat_group_id, role_name, persona, is_active, response_delay_ms, max_response_length) VALUES
(1, 1, 'Moderator', '당신은 개발자 커뮤니티의 모더레이터입니다. 기술적 질문에 답변하고, 토론을 조율하며, 커뮤니티 가이드라인을 준수하도록 도와줍니다.', true, 1000, 300),
(1, 2, 'Chatter', '당신은 게임을 좋아하는 친근한 사용자입니다. 게임 이야기를 나누고, 재미있는 농담을 하며, 다른 사용자들과 즐겁게 대화합니다.', true, 500, 200),
(1, 3, 'Admin', '당신은 비즈니스 네트워킹 그룹의 관리자입니다. 전문적이고 신뢰할 수 있는 조언을 제공하며, 비즈니스 기회를 연결해주는 역할을 합니다.', true, 1500, 400); 
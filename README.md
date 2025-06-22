# Telegram Agent Manager (Auth Server)

텔레그램 계정 인증 및 관리 전용 서버입니다. Supabase와 연동하여 데이터를 저장하고, 프론트엔드 대시보드와 연동됩니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   프론트엔드    │    │  파이썬 서버     │    │    Supabase     │
│   (대시보드)    │◄──►│  (인증 전용)    │◄──►│   (데이터 저장)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 각 서비스 역할

- **파이썬 서버**: 텔레그램 인증 처리, 세션 관리, Supabase 연동
- **Supabase**: 계정 정보, 페르소나 설정, 메시지 로그 저장
- **프론트엔드**: 대시보드, 설정 UI, 실시간 데이터 표시

## 🚀 주요 기능

- **텔레그램 인증**: Telethon을 사용한 안전한 인증
- **2FA 지원**: 2단계 인증 처리
- **세션 관리**: 세션 스트링 생성 및 저장
- **Supabase 연동**: 실시간 데이터 동기화
- **계정 관리**: 계정 CRUD 작업
- **연결 테스트**: 계정 상태 확인
- **대시보드 통계**: 실시간 통계 데이터

## 📋 시스템 요구사항

- Python 3.8+
- Supabase 계정
- 텔레그램 API ID & Hash

## 🛠️ 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd telegram-python-server
```

### 2. conda 환경 생성 및 활성화

```bash
conda create -n telegram-agents python=3.11 -y
conda activate telegram-agents
```

### 3. 의존성 설치

```bash
pip install fastapi uvicorn telethon python-dotenv openai pydantic python-multipart sqlalchemy requests supabase
```

### 4. 환경 변수 설정

```bash
copy env.example .env
```

`.env` 파일을 편집하여 Supabase 설정을 입력하세요:

```env
# Supabase 설정 (필수)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# OpenAI 설정 (선택사항)
OPENAI_API_KEY=your_openai_api_key_here

# 텔레그램 설정 (선택사항)
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
```

### 5. Supabase 데이터베이스 설정

1. Supabase 프로젝트 생성
2. SQL 편집기에서 `supabase_schema.sql` 실행
3. 테이블 및 정책 생성 완료

### 6. 서버 실행

```bash
python -m app.main
```

서버가 `http://localhost:8000`에서 실행됩니다.

## 📚 API 사용법

### 텔레그램 인증

#### 1. 인증 프로세스 시작

```bash
curl -X POST "http://localhost:8000/telegram-auth/start" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "api_id": 12345,
    "api_hash": "your_api_hash"
  }'
```

#### 2. 인증 코드 확인

```bash
curl -X POST "http://localhost:8000/telegram-auth/verify-code" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "code": "12345"
  }'
```

#### 3. 2FA 비밀번호 확인 (필요시)

```bash
curl -X POST "http://localhost:8000/telegram-auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "password": "your_2fa_password"
  }'
```

### 계정 관리

#### 계정 목록 조회

```bash
curl "http://localhost:8000/accounts/"
```

#### 계정 연결 테스트

```bash
curl -X POST "http://localhost:8000/telegram-auth/test-connection/1"
```

#### 세션 취소

```bash
curl -X POST "http://localhost:8000/telegram-auth/revoke-session/1"
```

### 대시보드 통계

```bash
curl "http://localhost:8000/telegram-auth/dashboard/stats"
```

## 🗄️ Supabase 데이터베이스 스키마

### 주요 테이블

- **accounts**: 계정 정보 및 세션 스트링
- **chat_groups**: 채팅방 정보
- **agent_roles**: 에이전트 역할 및 페르소나
- **message_logs**: 메시지 응답 로그
- **auth_sessions**: 인증 세션 관리

### 뷰

- **account_roles_view**: 계정별 역할 정보 통합 뷰

## 🔧 인증 프로세스

### 1단계: 인증 시작

1. 전화번호, API ID, API Hash 입력
2. 텔레그램에서 인증 코드 전송
3. 임시 클라이언트 생성

### 2단계: 코드 확인

1. 수신된 인증 코드 입력
2. 텔레그램 계정 인증
3. 2FA 필요시 3단계로 진행

### 3단계: 2FA 확인 (필요시)

1. 2FA 비밀번호 입력
2. 최종 인증 완료
3. 세션 스트링 생성 및 저장

### 4단계: 계정 저장

1. 계정 정보 Supabase에 저장
2. 세션 스트링 암호화 저장
3. 인증 완료

## 📊 대시보드 통계

- **총 계정 수**: 등록된 모든 계정
- **활성 계정 수**: 현재 활성화된 계정
- **총 역할 수**: 모든 에이전트 역할
- **활성 역할 수**: 현재 활성화된 역할
- **오늘 메시지 수**: 오늘 처리된 메시지

## 🚨 주의사항

1. **보안**: API 키와 세션 정보를 안전하게 관리
2. **텔레그램 정책**: 텔레그램 이용약관 준수
3. **Supabase 설정**: 올바른 프로젝트 URL과 키 사용
4. **2FA**: 2단계 인증이 활성화된 계정 지원

## 🔗 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인하세요:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🛠️ 개발

### 디버그 모드 실행

```bash
# .env 파일에서 DEBUG=True 설정
python -m app.main
```

### 로그 확인

- 서버 시작/종료 로그
- 인증 프로세스 로그
- Supabase 연동 로그

## 📞 지원

문제가 있거나 질문이 있으시면 이슈를 생성해 주세요.

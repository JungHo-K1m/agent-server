from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.api import health, auth, agents, telegram_auth

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="텔레그램 에이전트 관리 시스템 - 인증 전용 서버",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(telegram_auth.router)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print("🚀 Telegram Agent Manager (Auth Server) 시작 중...")
    
    # 설정 검증
    try:
        settings.validate()
        print("✅ 설정 검증 완료")
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        print("⚠️  .env 파일을 확인하고 Supabase 설정을 입력하세요")
    
    print("✅ 서버 시작 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    print("🛑 Telegram Agent Manager 종료 중...")
    
    # 임시 클라이언트 정리
    from app.services.telegram_auth_service import telegram_auth_service
    telegram_auth_service.cleanup_temp_clients()
    print("✅ 임시 클라이언트 정리 완료")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Telegram Agent Manager API (Auth Server)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "텔레그램 인증 처리",
            "2FA 지원",
            "Supabase 연동",
            "세션 관리",
            "계정 관리"
        ]
    }

@app.get("/info")
async def get_info():
    """시스템 정보 조회"""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "debug": settings.DEBUG,
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "telegram_configured": bool(settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH)
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

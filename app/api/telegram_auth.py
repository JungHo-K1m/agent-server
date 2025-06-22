from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.telegram_auth_service import telegram_auth_service
from app.services.supabase_service import supabase_service

router = APIRouter(prefix="/telegram-auth", tags=["telegram-authentication"])

# Pydantic 모델들
class AuthStartRequest(BaseModel):
    phone_number: str
    api_id: int
    api_hash: str

class CodeVerifyRequest(BaseModel):
    phone_number: str
    code: str

class TwoFactorRequest(BaseModel):
    phone_number: str
    password: str

@router.post("/start")
async def start_auth(request: AuthStartRequest):
    """텔레그램 인증 프로세스 시작"""
    try:
        result = await telegram_auth_service.start_auth_process(
            request.phone_number,
            request.api_id,
            request.api_hash
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인증 시작 실패: {str(e)}")

@router.post("/verify-code")
async def verify_code(request: CodeVerifyRequest):
    """인증 코드 확인"""
    try:
        result = await telegram_auth_service.verify_code(
            request.phone_number,
            request.code
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 확인 실패: {str(e)}")

@router.post("/verify-2fa")
async def verify_2fa(request: TwoFactorRequest):
    """2FA 비밀번호 확인"""
    try:
        result = await telegram_auth_service.verify_2fa(
            request.phone_number,
            request.password
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"2FA 확인 실패: {str(e)}")

@router.post("/test-connection/{account_id}")
async def test_connection(account_id: int):
    """계정 연결 테스트"""
    try:
        result = await telegram_auth_service.test_connection(account_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")

@router.post("/revoke-session/{account_id}")
async def revoke_session(account_id: int):
    """세션 취소"""
    try:
        result = await telegram_auth_service.revoke_session(account_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 취소 실패: {str(e)}")

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """대시보드 통계"""
    try:
        stats = await supabase_service.get_dashboard_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}") 
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Telegram Agent Manager"
    }

@router.get("/ping")
async def ping():
    """간단한 ping 응답"""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

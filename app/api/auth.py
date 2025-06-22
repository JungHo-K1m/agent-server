from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.account import Account
from app.services.telegram_auth_service import telegram_auth_service
from app.services.supabase_service import supabase_service

router = APIRouter(prefix="/accounts", tags=["accounts"])

class AccountCreateRequest(BaseModel):
    phone_number: str
    api_id: int
    api_hash: str
    session_string: str
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class AccountUpdateRequest(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

@router.post("/")
async def create_account(request: AccountCreateRequest, db: Session = Depends(get_db)):
    """새로운 계정 생성"""
    try:
        # 중복 확인
        existing = db.query(Account).filter(Account.phone_number == request.phone_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 전화번호입니다.")
        
        account = Account(
            phone_number=request.phone_number,
            api_id=request.api_id,
            api_hash=request.api_hash,
            session_string=request.session_string,
            user_id=request.user_id,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return {
            "success": True,
            "account": {
                "id": account.id,
                "phone_number": account.phone_number,
                "username": account.username,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "is_verified": account.is_verified,
                "is_active": account.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 생성 실패: {str(e)}")

@router.get("/")
async def get_accounts(db: Session = Depends(get_db)):
    """모든 계정 조회"""
    try:
        accounts = db.query(Account).all()
        
        account_list = []
        for account in accounts:
            account_list.append({
                "id": account.id,
                "phone_number": account.phone_number,
                "username": account.username,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "is_verified": account.is_verified,
                "is_active": account.is_active,
                "created_at": account.created_at
            })
        
        return {"success": True, "accounts": account_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 조회 실패: {str(e)}")

@router.get("/{account_id}")
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """특정 계정 조회"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "account": {
                "id": account.id,
                "phone_number": account.phone_number,
                "username": account.username,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "is_verified": account.is_verified,
                "is_active": account.is_active,
                "created_at": account.created_at,
                "updated_at": account.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 조회 실패: {str(e)}")

@router.put("/{account_id}")
async def update_account(account_id: int, request: AccountUpdateRequest, db: Session = Depends(get_db)):
    """계정 정보 수정"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        # 업데이트할 필드들
        if request.username is not None:
            account.username = request.username
        if request.first_name is not None:
            account.first_name = request.first_name
        if request.last_name is not None:
            account.last_name = request.last_name
        if request.is_verified is not None:
            account.is_verified = request.is_verified
        if request.is_active is not None:
            account.is_active = request.is_active
        
        db.commit()
        db.refresh(account)
        
        return {
            "success": True,
            "account": {
                "id": account.id,
                "phone_number": account.phone_number,
                "username": account.username,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "is_verified": account.is_verified,
                "is_active": account.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 수정 실패: {str(e)}")

@router.delete("/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """계정 삭제"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        db.delete(account)
        db.commit()
        
        return {"success": True, "message": "계정이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 삭제 실패: {str(e)}")

@router.post("/{account_id}/verify")
async def verify_account(account_id: int, db: Session = Depends(get_db)):
    """계정 인증"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        account.is_verified = True
        db.commit()
        
        return {"success": True, "message": "계정이 인증되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 인증 실패: {str(e)}")

@router.post("/{account_id}/activate")
async def activate_account(account_id: int, db: Session = Depends(get_db)):
    """계정 활성화"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        account.is_active = True
        db.commit()
        
        return {"success": True, "message": "계정이 활성화되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 활성화 실패: {str(e)}")

@router.post("/{account_id}/deactivate")
async def deactivate_account(account_id: int, db: Session = Depends(get_db)):
    """계정 비활성화"""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        account.is_active = False
        db.commit()
        
        return {"success": True, "message": "계정이 비활성화되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 비활성화 실패: {str(e)}")

@router.post("/auth/start")
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

@router.post("/auth/verify-code")
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

@router.post("/auth/verify-2fa")
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

@router.post("/auth/test-connection/{account_id}")
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

@router.post("/auth/revoke-session/{account_id}")
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

@router.post("/accounts")
async def create_account_supabase(request: AccountCreateRequest):
    """새로운 계정 생성 (수동)"""
    try:
        # 중복 확인
        existing = await supabase_service.get_account_by_phone(request.phone_number)
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 전화번호입니다.")
        
        account_data = {
            "phone_number": request.phone_number,
            "api_id": request.api_id,
            "api_hash": request.api_hash,
            "session_string": request.session_string,
            "user_id": request.user_id,
            "username": request.username,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "is_verified": True,
            "is_active": True
        }
        
        account = await supabase_service.create_account(account_data)
        
        return {
            "success": True,
            "account": account
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 생성 실패: {str(e)}")

@router.get("/accounts")
async def get_accounts_supabase():
    """모든 계정 조회"""
    try:
        accounts = await supabase_service.get_all_accounts()
        return {
            "success": True,
            "accounts": accounts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 조회 실패: {str(e)}")

@router.get("/accounts/{account_id}")
async def get_account_supabase(account_id: int):
    """특정 계정 조회"""
    try:
        account = await supabase_service.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "account": account
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 조회 실패: {str(e)}")

@router.put("/accounts/{account_id}")
async def update_account_supabase(account_id: int, request: AccountUpdateRequest):
    """계정 정보 수정"""
    try:
        # 업데이트할 데이터 구성
        update_data = {}
        if request.username is not None:
            update_data["username"] = request.username
        if request.first_name is not None:
            update_data["first_name"] = request.first_name
        if request.last_name is not None:
            update_data["last_name"] = request.last_name
        if request.is_verified is not None:
            update_data["is_verified"] = request.is_verified
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        account = await supabase_service.update_account(account_id, update_data)
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "account": account
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 수정 실패: {str(e)}")

@router.delete("/accounts/{account_id}")
async def delete_account_supabase(account_id: int):
    """계정 삭제"""
    try:
        # 계정 비활성화로 처리
        account = await supabase_service.update_account(account_id, {"is_active": False})
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": "계정이 비활성화되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 삭제 실패: {str(e)}")

@router.post("/accounts/{account_id}/verify")
async def verify_account_supabase(account_id: int):
    """계정 인증"""
    try:
        account = await supabase_service.update_account(account_id, {"is_verified": True})
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": "계정이 인증되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 인증 실패: {str(e)}")

@router.post("/accounts/{account_id}/activate")
async def activate_account_supabase(account_id: int):
    """계정 활성화"""
    try:
        account = await supabase_service.update_account(account_id, {"is_active": True})
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": "계정이 활성화되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 활성화 실패: {str(e)}")

@router.post("/accounts/{account_id}/deactivate")
async def deactivate_account_supabase(account_id: int):
    """계정 비활성화"""
    try:
        account = await supabase_service.update_account(account_id, {"is_active": False})
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": "계정이 비활성화되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"계정 비활성화 실패: {str(e)}")

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

@router.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 임시 클라이언트 정리"""
    telegram_auth_service.cleanup_temp_clients()

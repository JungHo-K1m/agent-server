from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from app.database import get_db
from app.services.agent_service import agent_service
from app.models.account import Account
from app.models.agent import AgentRole, ChatGroup
from app.models.message_log import MessageLog

router = APIRouter(prefix="/agents", tags=["agents"])

# Pydantic 모델들
class RoleCreateRequest(BaseModel):
    account_id: int
    chat_id: int
    role_name: str
    persona: str
    openai_api_key: Optional[str] = None
    response_delay_ms: Optional[int] = 0
    max_response_length: Optional[int] = 500

class RoleUpdateRequest(BaseModel):
    role_name: Optional[str] = None
    persona: Optional[str] = None
    openai_api_key: Optional[str] = None
    response_delay_ms: Optional[int] = None
    max_response_length: Optional[int] = None
    is_active: Optional[bool] = None

class AccountCreateRequest(BaseModel):
    phone_number: str
    api_id: int
    api_hash: str
    session_string: str
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@router.post("/start")
async def start_all_agents(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """모든 활성 에이전트 시작"""
    try:
        background_tasks.add_task(agent_service.start_all_agents, db)
        return {"success": True, "message": "에이전트 시작 요청이 처리되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에이전트 시작 실패: {str(e)}")

@router.post("/stop")
async def stop_all_agents():
    """모든 에이전트 중지"""
    try:
        await agent_service.stop_all_agents()
        return {"success": True, "message": "모든 에이전트가 중지되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에이전트 중지 실패: {str(e)}")

@router.get("/status")
async def get_agents_status():
    """활성 에이전트 상태 조회"""
    try:
        active_agents = agent_service.get_active_agents()
        return {
            "success": True,
            "active_agents": active_agents,
            "total_agents": len(active_agents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

@router.post("/roles")
async def create_role(request: RoleCreateRequest, db: Session = Depends(get_db)):
    """새로운 역할 생성"""
    try:
        # 계정 존재 확인
        account = db.query(Account).filter(Account.id == request.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
        
        # 역할 추가
        role = await agent_service.add_role_to_chat(
            account_id=request.account_id,
            chat_id=request.chat_id,
            role_name=request.role_name,
            persona=request.persona,
            openai_api_key=request.openai_api_key,
            response_delay_ms=request.response_delay_ms,
            max_response_length=request.max_response_length,
            db=db
        )
        
        return {
            "success": True,
            "role": {
                "id": role.id,
                "role_name": role.role_name,
                "persona": role.persona,
                "chat_id": request.chat_id,
                "account_id": request.account_id
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"역할 생성 실패: {str(e)}")

@router.get("/accounts/{account_id}/roles")
async def get_account_roles(account_id: int, db: Session = Depends(get_db)):
    """계정의 모든 역할 조회"""
    try:
        roles = db.query(AgentRole).join(ChatGroup).filter(
            AgentRole.account_id == account_id
        ).all()
        
        role_list = []
        for role in roles:
            role_list.append({
                "id": role.id,
                "role_name": role.role_name,
                "persona": role.persona,
                "chat_id": role.chat_group.chat_id,
                "chat_title": role.chat_group.chat_title,
                "is_active": role.is_active,
                "response_delay_ms": role.response_delay_ms,
                "max_response_length": role.max_response_length,
                "created_at": role.created_at
            })
        
        return {"success": True, "roles": role_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"역할 조회 실패: {str(e)}")

@router.put("/roles/{role_id}")
async def update_role(role_id: int, request: RoleUpdateRequest, db: Session = Depends(get_db)):
    """역할 정보 수정"""
    try:
        role = db.query(AgentRole).filter(AgentRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다.")
        
        # 업데이트할 필드들
        update_data = {}
        if request.role_name is not None:
            update_data["role_name"] = request.role_name
        if request.persona is not None:
            update_data["persona"] = request.persona
        if request.openai_api_key is not None:
            update_data["openai_api_key"] = request.openai_api_key
        if request.response_delay_ms is not None:
            update_data["response_delay_ms"] = request.response_delay_ms
        if request.max_response_length is not None:
            update_data["max_response_length"] = request.max_response_length
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        # 데이터베이스 업데이트
        for key, value in update_data.items():
            setattr(role, key, value)
        
        db.commit()
        db.refresh(role)
        
        # 활성 클라이언트의 역할 정보도 업데이트
        if role.account_id in agent_service.active_clients:
            chat_id = role.chat_group.chat_id
            if chat_id in agent_service.role_handlers.get(role.account_id, {}):
                agent_service.role_handlers[role.account_id][chat_id].update({
                    "role_name": role.role_name,
                    "persona": role.persona,
                    "openai_api_key": role.openai_api_key,
                    "response_delay_ms": role.response_delay_ms,
                    "max_response_length": role.max_response_length
                })
        
        return {
            "success": True,
            "role": {
                "id": role.id,
                "role_name": role.role_name,
                "persona": role.persona,
                "is_active": role.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"역할 수정 실패: {str(e)}")

@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """역할 삭제"""
    try:
        role = db.query(AgentRole).filter(AgentRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다.")
        
        # 활성 클라이언트에서 역할 제거
        if role.account_id in agent_service.active_clients:
            chat_id = role.chat_group.chat_id
            if chat_id in agent_service.role_handlers.get(role.account_id, {}):
                del agent_service.role_handlers[role.account_id][chat_id]
        
        db.delete(role)
        db.commit()
        
        return {"success": True, "message": "역할이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"역할 삭제 실패: {str(e)}")

@router.get("/roles/{role_id}/logs")
async def get_role_logs(role_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """역할별 메시지 로그 조회"""
    try:
        logs = db.query(MessageLog).filter(
            MessageLog.agent_role_id == role_id
        ).order_by(MessageLog.created_at.desc()).limit(limit).all()
        
        log_list = []
        for log in logs:
            log_list.append({
                "id": log.id,
                "chat_id": log.chat_id,
                "user_id": log.user_id,
                "message_text": log.message_text,
                "response_text": log.response_text,
                "response_time_ms": log.response_time_ms,
                "role_used": log.role_used,
                "created_at": log.created_at
            })
        
        return {"success": True, "logs": log_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {str(e)}")

@router.get("/chats")
async def get_chat_groups(db: Session = Depends(get_db)):
    """모든 채팅방 조회"""
    try:
        chats = db.query(ChatGroup).all()
        
        chat_list = []
        for chat in chats:
            chat_list.append({
                "id": chat.id,
                "chat_id": chat.chat_id,
                "chat_title": chat.chat_title,
                "chat_type": chat.chat_type,
                "is_active": chat.is_active,
                "created_at": chat.created_at
            })
        
        return {"success": True, "chats": chat_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")

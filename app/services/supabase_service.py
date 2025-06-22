from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import os
from datetime import datetime, timedelta
import uuid

from app.config import settings

class SupabaseService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    # 계정 관리
    async def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """계정 생성"""
        try:
            result = self.supabase.table("accounts").insert(account_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating account: {e}")
            raise
    
    async def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """계정 조회"""
        try:
            result = self.supabase.table("accounts").select("*").eq("id", account_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting account: {e}")
            return None
    
    async def get_account_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """전화번호로 계정 조회"""
        try:
            result = self.supabase.table("accounts").select("*").eq("phone_number", phone_number).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting account by phone: {e}")
            return None
    
    async def update_account(self, account_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """계정 정보 업데이트"""
        try:
            result = self.supabase.table("accounts").update(update_data).eq("id", account_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating account: {e}")
            return None
    
    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """모든 계정 조회"""
        try:
            result = self.supabase.table("accounts").select("*").execute()
            return result.data
        except Exception as e:
            print(f"Error getting all accounts: {e}")
            return []
    
    # 채팅방 관리
    async def create_chat_group(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """채팅방 생성"""
        try:
            result = self.supabase.table("chat_groups").insert(chat_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating chat group: {e}")
            raise
    
    async def get_chat_group(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """채팅방 조회"""
        try:
            result = self.supabase.table("chat_groups").select("*").eq("chat_id", chat_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting chat group: {e}")
            return None
    
    async def get_or_create_chat_group(self, chat_id: int, chat_title: str = None) -> Dict[str, Any]:
        """채팅방 조회 또는 생성"""
        existing = await self.get_chat_group(chat_id)
        if existing:
            return existing
        
        chat_data = {
            "chat_id": chat_id,
            "chat_title": chat_title or f"Chat {chat_id}",
            "chat_type": "supergroup",
            "is_active": True
        }
        return await self.create_chat_group(chat_data)
    
    # 에이전트 역할 관리
    async def create_agent_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 역할 생성"""
        try:
            result = self.supabase.table("agent_roles").insert(role_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating agent role: {e}")
            raise
    
    async def get_account_roles(self, account_id: int) -> List[Dict[str, Any]]:
        """계정의 모든 역할 조회"""
        try:
            result = self.supabase.table("agent_roles").select(
                "*, chat_groups(*)"
            ).eq("account_id", account_id).execute()
            return result.data
        except Exception as e:
            print(f"Error getting account roles: {e}")
            return []
    
    async def get_active_roles(self, account_id: int) -> List[Dict[str, Any]]:
        """계정의 활성 역할 조회"""
        try:
            result = self.supabase.table("agent_roles").select(
                "*, chat_groups(*)"
            ).eq("account_id", account_id).eq("is_active", True).execute()
            return result.data
        except Exception as e:
            print(f"Error getting active roles: {e}")
            return []
    
    async def update_agent_role(self, role_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """에이전트 역할 업데이트"""
        try:
            result = self.supabase.table("agent_roles").update(update_data).eq("id", role_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating agent role: {e}")
            return None
    
    async def delete_agent_role(self, role_id: int) -> bool:
        """에이전트 역할 삭제"""
        try:
            result = self.supabase.table("agent_roles").delete().eq("id", role_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting agent role: {e}")
            return False
    
    # 메시지 로그 관리
    async def save_message_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 로그 저장"""
        try:
            result = self.supabase.table("message_logs").insert(log_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving message log: {e}")
            raise
    
    async def get_role_logs(self, role_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """역할별 메시지 로그 조회"""
        try:
            result = self.supabase.table("message_logs").select("*").eq(
                "agent_role_id", role_id
            ).order("created_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"Error getting role logs: {e}")
            return []
    
    # 인증 세션 관리
    async def create_auth_session(self, account_id: int) -> Dict[str, Any]:
        """인증 세션 생성"""
        try:
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
            
            session_data = {
                "account_id": account_id,
                "session_token": session_token,
                "is_verified": False,
                "expires_at": expires_at.isoformat()
            }
            
            result = self.supabase.table("auth_sessions").insert(session_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating auth session: {e}")
            raise
    
    async def get_auth_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """인증 세션 조회"""
        try:
            result = self.supabase.table("auth_sessions").select("*").eq(
                "session_token", session_token
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting auth session: {e}")
            return None
    
    async def update_auth_session(self, session_token: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """인증 세션 업데이트"""
        try:
            result = self.supabase.table("auth_sessions").update(update_data).eq(
                "session_token", session_token
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating auth session: {e}")
            return None
    
    async def delete_auth_session(self, session_token: str) -> bool:
        """인증 세션 삭제"""
        try:
            result = self.supabase.table("auth_sessions").delete().eq(
                "session_token", session_token
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting auth session: {e}")
            return False
    
    # 통계 및 대시보드 데이터
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 통계 데이터"""
        try:
            # 계정 수
            accounts_result = self.supabase.table("accounts").select("id", count="exact").execute()
            total_accounts = accounts_result.count or 0
            
            # 활성 계정 수
            active_accounts_result = self.supabase.table("accounts").select(
                "id", count="exact"
            ).eq("is_active", True).execute()
            active_accounts = active_accounts_result.count or 0
            
            # 총 역할 수
            roles_result = self.supabase.table("agent_roles").select("id", count="exact").execute()
            total_roles = roles_result.count or 0
            
            # 활성 역할 수
            active_roles_result = self.supabase.table("agent_roles").select(
                "id", count="exact"
            ).eq("is_active", True).execute()
            active_roles = active_roles_result.count or 0
            
            # 오늘 메시지 수
            today = datetime.utcnow().date().isoformat()
            today_logs_result = self.supabase.table("message_logs").select(
                "id", count="exact"
            ).gte("created_at", today).execute()
            today_messages = today_logs_result.count or 0
            
            return {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "total_roles": total_roles,
                "active_roles": active_roles,
                "today_messages": today_messages
            }
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {
                "total_accounts": 0,
                "active_accounts": 0,
                "total_roles": 0,
                "active_roles": 0,
                "today_messages": 0
            }

# 전역 인스턴스
supabase_service = SupabaseService() 
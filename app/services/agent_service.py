import asyncio
import time
from typing import Dict, List, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from sqlalchemy.orm import Session
from sqlalchemy import and_
import openai
import os

from app.models.account import Account
from app.models.agent import ChatGroup, AgentRole
from app.models.message_log import MessageLog
from app.config import settings

class TelegramAgentService:
    def __init__(self):
        self.active_clients: Dict[int, TelegramClient] = {}
        self.role_handlers: Dict[int, Dict[int, dict]] = {}  # account_id -> {chat_id -> role_info}
        
        # OpenAI 설정
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def start_all_agents(self, db: Session):
        """모든 활성 에이전트 시작"""
        try:
            # 활성 계정들 가져오기
            accounts = db.query(Account).filter(Account.is_active == True).all()
            
            for account in accounts:
                await self.start_account_client(account, db)
                
            print(f"Started {len(accounts)} active agents")
            
        except Exception as e:
            print(f"Error starting agents: {e}")
    
    async def start_account_client(self, account: Account, db: Session):
        """개별 계정 클라이언트 시작"""
        account_id = account.id
        
        # 이미 실행 중인지 확인
        if account_id in self.active_clients:
            return
        
        try:
            # 텔레그램 클라이언트 생성
            client = TelegramClient(
                StringSession(account.session_string),
                account.api_id,
                account.api_hash
            )
            
            # 이벤트 핸들러 설정
            @client.on(events.NewMessage)
            async def handle_message(event):
                await self.process_message(event, account_id, db)
            
            # 클라이언트 시작
            await client.start()
            self.active_clients[account_id] = client
            self.role_handlers[account_id] = {}
            
            # 해당 계정의 모든 역할 정보 로드
            await self.load_account_roles(account_id, db)
            
            print(f"Account {account.phone_number} started successfully")
            
        except Exception as e:
            print(f"Failed to start account {account.phone_number}: {e}")
    
    async def load_account_roles(self, account_id: int, db: Session):
        """계정의 모든 역할 정보 로드"""
        try:
            roles = db.query(AgentRole).join(ChatGroup).filter(
                and_(
                    AgentRole.account_id == account_id,
                    AgentRole.is_active == True,
                    ChatGroup.is_active == True
                )
            ).all()
            
            for role in roles:
                chat_id = role.chat_group.chat_id
                self.role_handlers[account_id][chat_id] = {
                    "id": role.id,
                    "role_name": role.role_name,
                    "persona": role.persona,
                    "openai_api_key": role.openai_api_key,
                    "response_delay_ms": role.response_delay_ms,
                    "max_response_length": role.max_response_length
                }
                
            print(f"Loaded {len(roles)} roles for account {account_id}")
            
        except Exception as e:
            print(f"Error loading roles for account {account_id}: {e}")
    
    async def process_message(self, event, account_id: int, db: Session):
        """메시지 처리 및 응답"""
        try:
            # 자기 자신의 메시지는 무시
            if event.sender_id == event.client.get_me().id:
                return
            
            chat_id = event.chat_id
            
            # 해당 채팅방에서의 역할 확인
            if account_id not in self.role_handlers or chat_id not in self.role_handlers[account_id]:
                return  # 이 채팅방에서는 역할이 없음
            
            role_info = self.role_handlers[account_id][chat_id]
            
            # 역할별 응답 생성
            start_time = time.time()
            
            response_text = await self.generate_role_response(
                event.message.text,
                role_info
            )
            
            # 응답 지연 (설정된 경우)
            if role_info.get("response_delay_ms", 0) > 0:
                await asyncio.sleep(role_info["response_delay_ms"] / 1000)
            
            # 응답 전송
            await event.reply(response_text)
            
            # 응답 시간 계산
            response_time = int((time.time() - start_time) * 1000)
            
            # 로그 저장
            await self.save_message_log(
                role_info["id"],
                chat_id,
                event.sender_id,
                event.message.text,
                response_text,
                response_time,
                role_info["role_name"],
                db
            )
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    async def generate_role_response(self, message: str, role_info: dict) -> str:
        """역할별 OpenAI 응답 생성"""
        try:
            # 역할별 API 키 사용 (있는 경우)
            api_key = role_info.get("openai_api_key") or settings.OPENAI_API_KEY
            if not api_key:
                return "OpenAI API 키가 설정되지 않았습니다."
            
            # 역할별 페르소나와 시스템 프롬프트 구성
            system_prompt = f"""
당신은 텔레그램 그룹에서 '{role_info['role_name']}' 역할을 맡고 있습니다.

역할: {role_info['role_name']}
페르소나: {role_info['persona']}

규칙:
1. 항상 지정된 역할과 페르소나에 맞게 응답하세요
2. 응답은 {role_info.get('max_response_length', 500)}자 이내로 작성하세요
3. 자연스럽고 대화에 적합한 톤을 유지하세요
4. 역할에 맞지 않는 내용은 피하세요
"""
            
            # OpenAI 클라이언트 생성
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=role_info.get("max_response_length", 500),
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
    
    async def save_message_log(self, role_id: int, chat_id: int, user_id: int, 
                              message: str, response: str, response_time: int, 
                              role_used: str, db: Session):
        """메시지 로그 저장"""
        try:
            log = MessageLog(
                agent_role_id=role_id,
                chat_id=chat_id,
                user_id=user_id,
                message_text=message,
                response_text=response,
                response_time_ms=response_time,
                role_used=role_used
            )
            
            db.add(log)
            db.commit()
            
        except Exception as e:
            print(f"Failed to save message log: {e}")
            db.rollback()
    
    async def add_role_to_chat(self, account_id: int, chat_id: int, role_name: str, 
                              persona: str, openai_api_key: str = None, 
                              response_delay_ms: int = 0, max_response_length: int = 500,
                              db: Session = None) -> AgentRole:
        """새로운 역할을 채팅방에 추가"""
        try:
            # 채팅방 정보 확인 또는 생성
            chat_group = await self.get_or_create_chat_group(chat_id, db)
            
            # 역할 추가
            role = AgentRole(
                account_id=account_id,
                chat_group_id=chat_group.id,
                role_name=role_name,
                persona=persona,
                is_active=True,
                openai_api_key=openai_api_key,
                response_delay_ms=response_delay_ms,
                max_response_length=max_response_length
            )
            
            db.add(role)
            db.commit()
            db.refresh(role)
            
            # 활성 클라이언트에 역할 정보 추가
            if account_id in self.active_clients:
                self.role_handlers[account_id][chat_id] = {
                    "id": role.id,
                    "role_name": role.role_name,
                    "persona": role.persona,
                    "openai_api_key": role.openai_api_key,
                    "response_delay_ms": role.response_delay_ms,
                    "max_response_length": role.max_response_length
                }
            
            return role
            
        except Exception as e:
            print(f"Failed to add role: {e}")
            db.rollback()
            raise
    
    async def get_or_create_chat_group(self, chat_id: int, db: Session) -> ChatGroup:
        """채팅방 정보 가져오기 또는 생성"""
        try:
            existing = db.query(ChatGroup).filter(ChatGroup.chat_id == chat_id).first()
            
            if existing:
                return existing
            
            # 새 채팅방 생성 (기본 정보)
            new_chat = ChatGroup(
                chat_id=chat_id,
                chat_title=f"Chat {chat_id}",
                chat_type="group",
                is_active=True
            )
            
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)
            
            return new_chat
            
        except Exception as e:
            print(f"Error creating chat group: {e}")
            db.rollback()
            raise
    
    async def stop_all_agents(self):
        """모든 에이전트 중지"""
        for account_id, client in self.active_clients.items():
            try:
                await client.disconnect()
                print(f"Stopped agent {account_id}")
            except Exception as e:
                print(f"Error stopping agent {account_id}: {e}")
        
        self.active_clients.clear()
        self.role_handlers.clear()
    
    def get_active_agents(self) -> Dict[int, Dict]:
        """활성 에이전트 정보 반환"""
        return {
            account_id: {
                "phone_number": client.session.phone if hasattr(client, 'session') else "Unknown",
                "roles": list(roles.keys()) if roles else []
            }
            for account_id, client in self.active_clients.items()
            for roles in [self.role_handlers.get(account_id, {})]
        }

# 전역 인스턴스
agent_service = TelegramAgentService()

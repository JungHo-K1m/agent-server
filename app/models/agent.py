from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ChatGroup(Base):
    __tablename__ = "chat_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True, nullable=False)  # 텔레그램 채팅 ID
    chat_title = Column(String(255))
    chat_type = Column(String(50))  # 'group', 'supergroup', 'channel'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    agent_roles = relationship("AgentRole", back_populates="chat_group")
    
    def __repr__(self):
        return f"<ChatGroup(id={self.id}, chat_id={self.chat_id}, title='{self.chat_title}')>"

class AgentRole(Base):
    __tablename__ = "agent_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    chat_group_id = Column(Integer, ForeignKey("chat_groups.id"), nullable=False)
    role_name = Column(String(50), nullable=False)  # 'Chatter', 'Moderator', 'Admin'
    persona = Column(Text, nullable=False)  # 해당 역할의 페르소나
    is_active = Column(Boolean, default=True)
    openai_api_key = Column(String(100))  # 개별 역할별 OpenAI 키
    response_delay_ms = Column(Integer, default=0)  # 응답 지연 시간
    max_response_length = Column(Integer, default=500)  # 최대 응답 길이
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    account = relationship("Account", back_populates="agent_roles")
    chat_group = relationship("ChatGroup", back_populates="agent_roles")
    message_logs = relationship("MessageLog", back_populates="agent_role")
    
    def __repr__(self):
        return f"<AgentRole(id={self.id}, account_id={self.account_id}, role_name='{self.role_name}')>"

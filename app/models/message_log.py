from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_role_id = Column(Integer, ForeignKey("agent_roles.id"), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    message_text = Column(Text, nullable=False)
    response_text = Column(Text)
    response_time_ms = Column(Integer)
    role_used = Column(String(50))  # 실제 사용된 역할
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    agent_role = relationship("AgentRole", back_populates="message_logs")
    
    def __repr__(self):
        return f"<MessageLog(id={self.id}, chat_id={self.chat_id}, role_used='{self.role_used}')>"

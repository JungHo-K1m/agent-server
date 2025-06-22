from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    api_id = Column(Integer, nullable=False)
    api_hash = Column(String(32), nullable=False)
    session_string = Column(String, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    agent_roles = relationship("AgentRole", back_populates="account")
    
    def __repr__(self):
        return f"<Account(id={self.id}, phone_number='{self.phone_number}', username='{self.username}')>"

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 모든 모델 import (테이블 생성용)
from app.models import Account, ChatGroup, AgentRole, MessageLog

load_dotenv()

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telegram_agents.db")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 데이터베이스 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테이블 생성 함수
def create_tables():
    # 모든 모델의 Base 클래스들을 하나로 통합
    from app.models.account import Base as AccountBase
    from app.models.agent import Base as AgentBase
    from app.models.message_log import Base as MessageLogBase
    
    # 모든 Base 클래스의 메타데이터를 통합
    metadata = AccountBase.metadata
    metadata.create_all(bind=engine)

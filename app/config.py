import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./telegram_agents.db")
    
    # Supabase 설정 (필수)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # 텔레그램 설정
    TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    
    # 애플리케이션 설정
    APP_NAME: str = "Telegram Agent Manager"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # 기본 응답 설정
    DEFAULT_RESPONSE_DELAY_MS: int = int(os.getenv("DEFAULT_RESPONSE_DELAY_MS", "0"))
    DEFAULT_MAX_RESPONSE_LENGTH: int = int(os.getenv("DEFAULT_MAX_RESPONSE_LENGTH", "500"))
    
    # 인증 설정
    SESSION_EXPIRE_HOURS: int = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))
    
    # CORS 설정
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    def validate(self):
        """필수 설정 검증"""
        required_fields = [
            ("SUPABASE_URL", self.SUPABASE_URL),
            ("SUPABASE_KEY", self.SUPABASE_KEY),
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")

settings = Settings()

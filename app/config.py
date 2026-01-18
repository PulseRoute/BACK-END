"""
설정 파일
환경 변수 로드 및 애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24시간
    
    # Firebase 설정
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"
    
    # ML 서버 설정
    ML_SERVER_URL: str = "http://ml-server:8000"
    ML_SERVER_TIMEOUT: int = 30
    
    # 검색 설정
    MAX_HOSPITAL_SEARCH_RADIUS_KM: float = 50.0
    
    # 애플리케이션 설정
    APP_NAME: str = "PulseRoute API"
    APP_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

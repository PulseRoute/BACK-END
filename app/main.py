"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.api import auth, patients, hospitals, requests, history, chat

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="응급환자 이송 매칭 시스템 API",
)

# CORS 미들웨어 설정 - 가장 먼저 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "https://pulseroute.vercel.app"
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(patients.router, prefix="/api/patients", tags=["환자"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["병원"])
app.include_router(requests.router, prefix="/api/requests", tags=["요청"])
app.include_router(history.router, prefix="/api/history", tags=["히스토리"])
app.include_router(chat.router, prefix="/api/chat", tags=["채팅"])


@app.get("/health", tags=["헬스체크"])
async def health_check():
    """
    서버 헬스체크
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8110,
        reload=True,
    )

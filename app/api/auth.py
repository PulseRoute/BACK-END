"""
인증 API 라우터
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService
import logging

router = APIRouter()
auth_service = AuthService()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    사용자 로그인
    
    - **email**: 사용자 이메일
    - **password**: 사용자 비밀번호
    
    반환:
    - 액세스 토큰
    - 사용자 정보
    """
    result = auth_service.login(request.email, request.password)
    
    if not result:
        logger.warning(f"로그인 실패: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다",
        )
    
    return result

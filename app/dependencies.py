"""
의존성 주입 모듈
FastAPI 엔드포인트에서 사용할 의존성 함수들
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.requests import Request
from app.utils.jwt_handler import JWTHandler
from app.utils.firebase_client import FirebaseClient
from typing import Dict, Any

security = HTTPBearer()
jwt_handler = JWTHandler()
firebase_client = FirebaseClient()


async def get_current_user(
    request: Request,
) -> Dict[str, Any]:
    """
    현재 사용자 정보를 JWT 토큰에서 추출
    
    Args:
        request: HTTP 요청
        
    Returns:
        사용자 정보 딕셔너리
        
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 헤더가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    payload = jwt_handler.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_ems_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    현재 EMS 사용자 정보 조회
    
    Args:
        current_user: 현재 사용자 정보
        
    Returns:
        EMS 사용자 정보
        
    Raises:
        HTTPException: 사용자 타입이 EMS가 아닌 경우
    """
    if current_user.get("type") != "ems":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMS 사용자만 접근할 수 있습니다",
        )
    
    return current_user


async def get_current_hospital_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    현재 병원 사용자 정보 조회
    
    Args:
        current_user: 현재 사용자 정보
        
    Returns:
        병원 사용자 정보
        
    Raises:
        HTTPException: 사용자 타입이 hospital이 아닌 경우
    """
    if current_user.get("type") != "hospital":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="병원 사용자만 접근할 수 있습니다",
        )
    
    return current_user

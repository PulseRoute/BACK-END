"""
JWT 핸들러
토큰 생성 및 검증
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class JWTHandler:
    """JWT 토큰 처리 클래스"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        액세스 토큰 생성
        
        Args:
            data: 토큰에 포함할 데이터
            
        Returns:
            JWT 토큰 문자열
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm,
            )
            logger.info(f"토큰 생성 성공: user_id={data.get('user_id')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"토큰 생성 실패: {str(e)}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        토큰 검증 및 페이로드 추출
        
        Args:
            token: JWT 토큰
            
        Returns:
            토큰 페이로드 또는 None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            logger.info(f"토큰 검증 성공: user_id={payload.get('user_id')}")
            return payload
        except JWTError as e:
            logger.error(f"토큰 검증 실패: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"토큰 검증 중 예외 발생: {str(e)}")
            return None

"""
인증 서비스
로그인, 토큰 검증 등
"""
from app.utils.firebase_client import FirebaseClient
from app.utils.jwt_handler import JWTHandler
from app.utils.validators import validate_email
from passlib.context import CryptContext
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """인증 서비스"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
        self.jwt_handler = JWTHandler()
    
    def hash_password(self, password: str) -> str:
        """
        비밀번호 해싱
        
        Args:
            password: 원본 비밀번호
            
        Returns:
            해시된 비밀번호
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        비밀번호 검증
        
        Args:
            plain_password: 입력된 비밀번호
            hashed_password: 저장된 해시 비밀번호
            
        Returns:
            일치 여부
        """
        import hashlib
        import bcrypt
        
        # SHA256 해시 확인 (테스트 계정용)
        sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        if hashed_password == sha256_hash:
            return True
        
        # bcrypt 해시 확인
        try:
            password_bytes = plain_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        사용자 로그인
        
        Args:
            email: 이메일
            password: 비밀번호
            
        Returns:
            로그인 결과 (토큰, 사용자 정보 등) 또는 None
        """
        try:
            # 사용자 조회
            user = self.firebase_client.get_user_by_email(email)
            
            if not user:
                logger.warning(f"로그인 실패: 사용자 없음 - {email}")
                return None
            
            # 비밀번호 검증
            if not self.verify_password(password, user.get("password_hash", "")):
                logger.warning(f"로그인 실패: 잘못된 비밀번호 - {email}")
                return None
            
            # 토큰 생성
            token_data = {
                "user_id": user["id"],
                "email": user["email"],
                "type": user["type"],
                "name": user["name"],
            }
            access_token = self.jwt_handler.create_access_token(token_data)
            
            logger.info(f"로그인 성공: {email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user["id"],
                "user_type": user["type"],
                "user_name": user["name"],
            }
        except Exception as e:
            logger.error(f"로그인 중 에러: {str(e)}")
            return None
    
    def verify_token_and_get_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        토큰 검증 및 사용자 정보 조회
        
        Args:
            token: JWT 토큰
            
        Returns:
            사용자 정보 또는 None
        """
        try:
            payload = self.jwt_handler.verify_token(token)
            
            if not payload:
                return None
            
            user = self.firebase_client.get_user_by_id(payload.get("user_id"))
            return user
        except Exception as e:
            logger.error(f"토큰 검증 실패: {str(e)}")
            return None

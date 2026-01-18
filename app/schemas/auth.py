"""
인증 관련 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "ems01@example.com",
                "password": "securepass123",
            }
        }


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str
    user_name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "user_123",
                "user_type": "ems",
                "user_name": "Seoul EMS Unit 1",
            }
        }


class TokenPayload(BaseModel):
    """토큰 페이로드"""
    user_id: str
    email: str
    type: str
    name: str

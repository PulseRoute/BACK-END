"""
사용자 데이터 모델
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 모델"""
    email: EmailStr
    type: str  # "ems" 또는 "hospital"
    name: str


class UserCreate(UserBase):
    """사용자 생성 모델"""
    password: str


class UserInDB(UserBase):
    """데이터베이스 저장 모델"""
    id: str
    password_hash: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class User(UserBase):
    """응답 모델"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

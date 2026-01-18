"""
병원 데이터 모델
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HospitalBase(BaseModel):
    """병원 기본 모델"""
    name: str
    email: str
    latitude: float
    longitude: float
    specialty: List[str] = []  # 전문 분야 리스트
    available_beds: int = 0


class HospitalCreate(HospitalBase):
    """병원 생성 모델"""
    password: str


class HospitalInDB(HospitalBase):
    """데이터베이스 저장 모델"""
    id: str
    password_hash: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Hospital(HospitalBase):
    """응답 모델"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

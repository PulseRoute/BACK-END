"""
이송 요청 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransferRequestBase(BaseModel):
    """이송 요청 기본 모델"""
    patient_id: str
    ems_unit_id: str
    hospital_id: str


class TransferRequestCreate(TransferRequestBase):
    """이송 요청 생성 모델"""
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[int] = None


class TransferRequestInDB(TransferRequestBase):
    """데이터베이스 저장 모델"""
    id: str
    status: str  # "pending", "accepted", "rejected", "cancelled"
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransferRequest(TransferRequestBase):
    """응답 모델"""
    id: str
    status: str
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransferRequestUpdate(BaseModel):
    """이송 요청 수정 모델"""
    status: str
    rejection_reason: Optional[str] = None

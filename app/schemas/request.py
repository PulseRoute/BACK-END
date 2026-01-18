"""
이송 요청 관련 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransferRequestResponse(BaseModel):
    """이송 요청 응답"""
    id: str
    patient_id: str
    ems_unit_id: str
    hospital_id: str
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    status: str
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    recommendation_reason: Optional[str] = None
    total_beds: Optional[int] = None
    has_trauma_center: Optional[bool] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransferRequestCreateRequest(BaseModel):
    """이송 요청 생성 요청 (EMS에서 병원 선택 시)"""
    hospital_id: str
    hospital_name: str
    hospital_address: Optional[str] = None
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    recommendation_reason: Optional[str] = None
    total_beds: Optional[int] = None
    has_trauma_center: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "hospital_id": "106301305",
                "hospital_name": "STANFORD HEALTH CARE",
                "hospital_address": "300 PASTEUR DR, STANFORD",
                "ml_score": 185432.5,
                "distance_km": 45.23,
                "estimated_time_minutes": 68,
                "recommendation_reason": "소요시간 67.8분 (45.2km) | 대형거점병원",
                "total_beds": 613,
                "has_trauma_center": True,
            }
        }


class TransferRequestUpdateRequest(BaseModel):
    """이송 요청 수정 요청"""
    status: str  # "accepted" 또는 "rejected"
    rejection_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "rejection_reason": None,
            }
        }

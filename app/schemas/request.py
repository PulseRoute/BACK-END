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

"""
병원 관련 스키마
"""
from pydantic import BaseModel
from typing import List, Optional


class HospitalBase(BaseModel):
    """병원 기본 정보"""
    name: str
    email: str
    latitude: float
    longitude: float
    specialty: List[str] = []
    available_beds: int = 0


class HospitalResponse(HospitalBase):
    """병원 응답"""
    id: str
    
    class Config:
        from_attributes = True

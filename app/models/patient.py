"""
환자 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class Location(BaseModel):
    """위치 정보"""
    latitude: float
    longitude: float


class VitalSigns(BaseModel):
    """바이탈 사인 정보"""
    blood_pressure: Optional[str] = None
    pulse: Optional[int] = None
    temperature: Optional[float] = None


class PatientBase(BaseModel):
    """환자 기본 모델"""
    name: str
    age: int
    gender: str  # "M" 또는 "F"
    disease_code: str  # ICD-10 코드
    severity_code: str  # KTAS 코드
    location: Location
    vital_signs: Optional[VitalSigns] = None


class PatientCreate(PatientBase):
    """환자 생성 모델"""
    pass


class PatientInDB(PatientBase):
    """데이터베이스 저장 모델"""
    id: str
    ems_unit_id: str
    status: str  # "searching", "matched", "transferred"
    created_at: datetime
    
    class Config:
        from_attributes = True


class Patient(PatientBase):
    """응답 모델"""
    id: str
    ems_unit_id: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

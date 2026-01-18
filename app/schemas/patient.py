"""
환자 관련 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationSchema(BaseModel):
    """위치 정보"""
    latitude: float
    longitude: float


class VitalSignsSchema(BaseModel):
    """바이탈 사인"""
    blood_pressure: Optional[str] = None
    pulse: Optional[int] = None
    temperature: Optional[float] = None


class PatientRegisterRequest(BaseModel):
    """환자 등록 요청"""
    name: str
    age: int
    gender: str  # "M" 또는 "F"
    disease_code: str
    severity_code: str
    location: LocationSchema
    vital_signs: Optional[VitalSignsSchema] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "홍길동",
                "age": 45,
                "gender": "M",
                "disease_code": "I21.0",
                "severity_code": "KTAS_1",
                "location": {
                    "latitude": 37.5665,
                    "longitude": 126.9780,
                },
                "vital_signs": {
                    "blood_pressure": "120/80",
                    "pulse": 75,
                    "temperature": 36.5,
                },
            }
        }


class PatientResponse(BaseModel):
    """환자 응답"""
    id: str
    name: str
    age: int
    gender: str
    disease_code: str
    severity_code: str
    location: LocationSchema
    vital_signs: Optional[VitalSignsSchema] = None
    status: str
    ems_unit_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientRequestsResponse(BaseModel):
    """환자의 요청 상태 응답"""
    patient_id: str
    patient_name: str
    status: str
    requests: list

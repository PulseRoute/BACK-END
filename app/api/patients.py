"""
환자 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.patient import PatientRegisterRequest, PatientResponse, PatientRequestsResponse
from app.services.patient_service import PatientService
from app.dependencies import get_current_ems_user
from typing import Dict, Any
import logging

router = APIRouter()
patient_service = PatientService()
logger = logging.getLogger(__name__)


@router.post("", response_model=PatientResponse)
async def register_patient(
    request: PatientRegisterRequest,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    환자 등록 및 자동 병원 매칭
    
    - **name**: 환자 이름
    - **age**: 환자 나이
    - **gender**: 환자 성별 (M/F)
    - **disease_code**: 질병 코드 (ICD-10)
    - **severity_code**: 중증도 코드 (KTAS_1~5)
    - **location**: 위치 정보 (latitude, longitude)
    - **vital_signs**: 바이탈 사인 (선택사항)
    
    반환:
    - 등록된 환자 정보
    """
    try:
        patient = await patient_service.register_patient(
            current_user["user_id"],
            request.model_dump(),
        )
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="환자 등록에 실패했습니다",
            )
        
        logger.info(f"환자 등록 완료: {current_user['user_id']}")
        return patient
    except Exception as e:
        logger.error(f"환자 등록 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="환자 등록 중 오류가 발생했습니다",
        )


@router.get("/{patient_id}/requests", response_model=PatientRequestsResponse)
async def get_patient_requests(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    환자의 요청 상태 조회
    
    - **patient_id**: 환자 ID
    
    반환:
    - 환자 정보
    - 병원별 이송 요청 상태
    """
    try:
        result = patient_service.get_patient_requests(patient_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="환자를 찾을 수 없습니다",
            )
        
        logger.info(f"환자 요청 조회: {patient_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"환자 요청 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요청 조회 중 오류가 발생했습니다",
        )

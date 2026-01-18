"""
환자 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.patient import PatientRegisterRequest, PatientResponse, PatientRequestsResponse, PatientListResponse
from app.schemas.request import TransferRequestCreateRequest, TransferRequestResponse
from app.services.patient_service import PatientService
from app.dependencies import get_current_ems_user
from typing import Dict, Any
import logging

router = APIRouter()
patient_service = PatientService()
logger = logging.getLogger(__name__)


@router.get("", response_model=PatientListResponse)
async def get_patients(
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    활성 환자 목록 조회 (해결된 환자 제외)

    - 현재 EMS 사용자가 등록한 환자만 조회
    - status가 transferred인 환자는 제외

    반환:
    - patients: 환자 목록
    - total: 총 환자 수
    """
    try:
        patients = patient_service.get_active_patients(current_user["user_id"])

        logger.info(f"환자 목록 조회: {current_user['user_id']}, {len(patients)}명")
        return {
            "patients": patients,
            "total": len(patients),
        }
    except Exception as e:
        logger.error(f"환자 목록 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="환자 목록 조회 중 오류가 발생했습니다",
        )


@router.post("", response_model=PatientResponse)
async def register_patient(
    request: PatientRegisterRequest,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    환자 등록 및 병원 추천

    환자 정보를 등록하고 ML을 통해 추천 병원 목록을 반환합니다.
    이송 요청은 별도의 API (POST /{patient_id}/request)를 통해 생성합니다.

    - **name**: 환자 이름
    - **age**: 환자 나이
    - **gender**: 환자 성별 (M/F)
    - **disease_code**: 질병 코드 (ICD-10)
    - **severity_code**: 중증도 코드 (KTAS_1~5)
    - **location**: 위치 정보 (latitude, longitude)
    - **vital_signs**: 바이탈 사인 (선택사항)

    반환:
    - 등록된 환자 정보 + matched_hospitals (추천 병원 목록)
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


@router.post("/{patient_id}/retry-match", response_model=PatientResponse)
async def retry_match(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    ML 매칭 재시도

    searching 상태인 환자에 대해 ML 매칭을 다시 시도합니다.
    이송 요청은 별도의 API (POST /{patient_id}/request)를 통해 생성합니다.

    - **patient_id**: 환자 ID (status가 searching인 환자만 가능)

    반환:
    - 매칭 성공 시: 환자 정보 + matched_hospitals (추천 병원 목록)
    - 매칭 실패 시: 400 에러
    """
    try:
        patient = await patient_service.retry_match(patient_id)

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="매칭에 실패했습니다. 환자가 존재하지 않거나 searching 상태가 아닙니다.",
            )

        logger.info(f"ML 재매칭 성공: {patient_id}")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML 재매칭 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="매칭 재시도 중 오류가 발생했습니다",
        )


@router.post("/{patient_id}/complete", response_model=PatientResponse)
async def complete_transfer(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    환자 이송 완료 처리

    - **patient_id**: 환자 ID

    완료 시:
    - 환자 상태를 "transferred"로 변경
    - 본인이 등록한 환자만 완료 처리 가능

    반환:
    - 업데이트된 환자 정보
    """
    try:
        patient = patient_service.complete_transfer(patient_id, current_user["user_id"])

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="환자를 찾을 수 없거나 권한이 없습니다",
            )

        logger.info(f"이송 완료: {patient_id}")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이송 완료 처리 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이송 완료 처리 중 오류가 발생했습니다",
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


@router.post("/{patient_id}/request", response_model=TransferRequestResponse)
async def create_transfer_request(
    patient_id: str,
    request: TransferRequestCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_ems_user),
):
    """
    특정 병원에 이송 요청 생성

    - **patient_id**: 환자 ID
    - **hospital_id**: 병원 ID (ML 매칭 결과의 facid)
    - **hospital_name**: 병원 이름
    - **hospital_address**: 병원 주소 (선택)
    - **ml_score**: ML 점수 (선택)
    - **distance_km**: 거리 (선택)
    - **estimated_time_minutes**: 예상 소요 시간 (선택)

    반환:
    - 생성된 이송 요청 정보
    """
    try:
        result = patient_service.create_transfer_request(
            patient_id,
            current_user["user_id"],
            request.model_dump(),
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이송 요청 생성에 실패했습니다. 환자가 존재하지 않거나 권한이 없습니다.",
            )

        logger.info(f"이송 요청 생성: {patient_id} -> {request.hospital_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이송 요청 생성 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이송 요청 생성 중 오류가 발생했습니다",
        )

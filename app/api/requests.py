"""
이송 요청 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.request import TransferRequestResponse, TransferRequestUpdateRequest
from app.services.hospital_service import HospitalService
from app.dependencies import get_current_hospital_user
from typing import Dict, Any
import logging

router = APIRouter()
hospital_service = HospitalService()
logger = logging.getLogger(__name__)


@router.post("/{request_id}/accept", response_model=TransferRequestResponse)
async def accept_request(
    request_id: str,
    current_user: Dict[str, Any] = Depends(get_current_hospital_user),
):
    """
    이송 요청 수락
    
    - **request_id**: 요청 ID
    
    수락 시:
    - 요청 상태를 "accepted"로 변경
    - 같은 환자의 다른 병원 요청들은 "cancelled"로 변경
    - 채팅방 자동 생성
    
    반환:
    - 업데이트된 요청 정보
    """
    try:
        result = hospital_service.accept_request(request_id, current_user["user_id"])
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="요청을 찾을 수 없거나 접근 권한이 없습니다",
            )
        
        logger.info(f"요청 수락: {request_id} - {current_user['user_id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요청 수락 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요청 처리 중 오류가 발생했습니다",
        )


@router.post("/{request_id}/reject", response_model=TransferRequestResponse)
async def reject_request(
    request_id: str,
    update: TransferRequestUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_hospital_user),
):
    """
    이송 요청 거부
    
    - **request_id**: 요청 ID
    - **rejection_reason**: 거부 사유
    
    반환:
    - 업데이트된 요청 정보
    """
    try:
        result = hospital_service.reject_request(
            request_id,
            current_user["user_id"],
            update.rejection_reason or "병상 부족",
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="요청을 찾을 수 없거나 접근 권한이 없습니다",
            )
        
        logger.info(f"요청 거부: {request_id} - {current_user['user_id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요청 거부 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요청 처리 중 오류가 발생했습니다",
        )

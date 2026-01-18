"""
병원 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.request import TransferRequestResponse
from app.services.hospital_service import HospitalService
from app.dependencies import get_current_hospital_user
from typing import Dict, Any, List
import logging

router = APIRouter()
hospital_service = HospitalService()
logger = logging.getLogger(__name__)


@router.get("/requests/pending", response_model=List[TransferRequestResponse])
async def get_pending_requests(
    current_user: Dict[str, Any] = Depends(get_current_hospital_user),
):
    """
    병원의 대기중인 이송 요청 목록 조회
    
    반환:
    - 대기중인 이송 요청 리스트
    """
    try:
        requests = hospital_service.get_pending_requests(current_user["user_id"])
        logger.info(f"대기 요청 조회: {current_user['user_id']} - {len(requests)}개")
        return requests
    except Exception as e:
        logger.error(f"대기 요청 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요청 조회 중 오류가 발생했습니다",
        )

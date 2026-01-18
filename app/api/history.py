"""
히스토리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.utils.firebase_client import FirebaseClient
from app.dependencies import get_current_user
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

router = APIRouter()
firebase_client = FirebaseClient()
logger = logging.getLogger(__name__)


@router.get("")
async def get_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
    severity_code: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    완료된 이송 기록 조회
    
    - **days**: 조회 기간 (기본값: 30일)
    - **severity_code**: 중증도 코드로 필터링 (선택사항)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20)
    
    반환:
    - 이송 기록 목록
    """
    try:
        user_id = current_user["user_id"]
        user_type = current_user["type"]
        
        # 완료된 요청 조회
        if not firebase_client._check_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터베이스 연결 실패",
            )
        
        # Firestore 쿼리
        query = firebase_client.db.collection("transfer_requests").where(
            "status", "==", "accepted"
        )
        docs = list(query.stream())
        
        # 사용자별 필터링
        records = []
        for doc in docs:
            record = doc.to_dict()
            record["id"] = doc.id
            
            if user_type == "ems" and record.get("ems_unit_id") != user_id:
                continue
            if user_type == "hospital" and record.get("hospital_id") != user_id:
                continue
            
            # 날짜 필터링
            created_at = record.get("created_at")
            if created_at:
                if (datetime.utcnow() - created_at).days > days:
                    continue
            
            # 중증도 필터링
            if severity_code:
                patient = firebase_client.get_patient(record.get("patient_id"))
                if not patient or patient.get("severity_code") != severity_code:
                    continue
            
            records.append(record)
        
        # 페이지네이션
        total = len(records)
        start = (page - 1) * limit
        end = start + limit
        paginated_records = records[start:end]
        
        logger.info(f"히스토리 조회: {user_id} - {len(paginated_records)}개")
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "records": paginated_records,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"히스토리 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="히스토리 조회 중 오류가 발생했습니다",
        )


@router.get("/{patient_id}/timeline")
async def get_patient_timeline(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    환자 이송 타임라인 조회
    
    - **patient_id**: 환자 ID
    
    반환:
    - 환자 등록 ~ 이송 완료까지의 전체 타임라인
    """
    try:
        # 환자 정보 조회
        patient = firebase_client.get_patient(patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="환자를 찾을 수 없습니다",
            )
        
        # 이송 요청 조회
        requests = firebase_client.get_requests_for_patient(patient_id)
        
        # 타임라인 구성
        timeline = [
            {
                "event": "환자 등록",
                "timestamp": patient.get("created_at"),
                "status": "completed",
                "description": f"{patient['name']} ({patient['age']}세) 환자 등록",
            }
        ]
        
        for req in requests:
            if req.get("status") == "pending":
                timeline.append({
                    "event": "요청 대기",
                    "timestamp": req.get("created_at"),
                    "status": "pending",
                    "description": f"병원에 이송 요청 대기 중",
                })
            elif req.get("status") == "accepted":
                timeline.append({
                    "event": "요청 수락",
                    "timestamp": req.get("updated_at"),
                    "status": "completed",
                    "description": f"병원에서 요청 수락",
                })
                
                # 채팅방 조회
                try:
                    docs = list(
                        firebase_client.db.collection("chat_rooms")
                        .where("patient_id", "==", patient_id)
                        .stream()
                    )
                    if docs:
                        timeline.append({
                            "event": "채팅 시작",
                            "timestamp": docs[0].to_dict().get("created_at"),
                            "status": "completed",
                            "description": "실시간 채팅 시작",
                        })
                except:
                    pass
        
        # 타임스탬프 순으로 정렬
        timeline.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.utcnow())
        
        logger.info(f"타임라인 조회: {patient_id}")
        
        return {
            "patient_id": patient_id,
            "patient_name": patient["name"],
            "timeline": timeline,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"타임라인 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="타임라인 조회 중 오류가 발생했습니다",
        )

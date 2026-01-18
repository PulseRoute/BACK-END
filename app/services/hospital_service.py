"""
병원 서비스
병원 요청 관리, 수락/거부 처리
"""
from app.utils.firebase_client import FirebaseClient
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HospitalService:
    """병원 서비스"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
    
    def get_pending_requests(self, hospital_id: str) -> List[Dict[str, Any]]:
        """
        병원의 대기중인 이송 요청 조회
        
        Args:
            hospital_id: 병원 ID
            
        Returns:
            대기중인 요청 목록
        """
        try:
            requests = self.firebase_client.get_pending_requests_for_hospital(hospital_id)
            
            # 각 요청에 환자 정보 추가
            for req in requests:
                patient = self.firebase_client.get_patient(req.get("patient_id"))
                if patient:
                    req["patient_info"] = patient
            
            logger.info(f"병원 대기 요청 조회: {hospital_id} - {len(requests)}개")
            return requests
        except Exception as e:
            logger.error(f"대기 요청 조회 실패: {str(e)}")
            return []
    
    def accept_request(self, request_id: str, hospital_id: str) -> Optional[Dict[str, Any]]:
        """
        이송 요청 수락
        - 해당 환자의 다른 병원 요청들은 자동 취소
        - 채팅방 자동 생성
        
        Args:
            request_id: 요청 ID
            hospital_id: 병원 ID
            
        Returns:
            업데이트된 요청 정보 또는 None
        """
        try:
            # 요청 조회
            request = self.firebase_client.get_transfer_request(request_id)
            
            if not request:
                logger.warning(f"요청을 찾을 수 없습니다: {request_id}")
                return None
            
            if request.get("hospital_id") != hospital_id:
                logger.warning(f"병원 ID 불일치: {request_id}")
                return None
            
            # 요청 상태 변경
            self.firebase_client.update_transfer_request(
                request_id,
                {"status": "accepted"},
            )
            
            # 같은 환자의 다른 병원 요청들 취소
            patient_id = request.get("patient_id")
            all_requests = self.firebase_client.get_requests_for_patient(patient_id)
            
            for req in all_requests:
                if req["id"] != request_id and req.get("status") == "pending":
                    self.firebase_client.update_transfer_request(
                        req["id"],
                        {"status": "cancelled"},
                    )
            
            # 채팅방 생성
            chat_room_data = {
                "patient_id": patient_id,
                "ems_unit_id": request.get("ems_unit_id"),
                "hospital_id": hospital_id,
                "is_active": True,
            }
            chat_room_id = self.firebase_client.create_chat_room(chat_room_data)
            
            logger.info(f"이송 요청 수락 성공: {request_id} - 채팅방: {chat_room_id}")
            
            # 업데이트된 요청 정보 반환
            updated_request = self.firebase_client.get_transfer_request(request_id)
            if updated_request:
                updated_request["chat_room_id"] = chat_room_id
            
            return updated_request
        except Exception as e:
            logger.error(f"요청 수락 실패: {str(e)}")
            return None
    
    def reject_request(self, request_id: str, hospital_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """
        이송 요청 거부
        
        Args:
            request_id: 요청 ID
            hospital_id: 병원 ID
            reason: 거부 사유
            
        Returns:
            업데이트된 요청 정보 또는 None
        """
        try:
            # 요청 조회
            request = self.firebase_client.get_transfer_request(request_id)
            
            if not request:
                logger.warning(f"요청을 찾을 수 없습니다: {request_id}")
                return None
            
            if request.get("hospital_id") != hospital_id:
                logger.warning(f"병원 ID 불일치: {request_id}")
                return None
            
            # 요청 상태 변경
            self.firebase_client.update_transfer_request(
                request_id,
                {
                    "status": "rejected",
                    "rejection_reason": reason,
                },
            )
            
            logger.info(f"이송 요청 거부 성공: {request_id} - 사유: {reason}")
            
            # 업데이트된 요청 정보 반환
            return self.firebase_client.get_transfer_request(request_id)
        except Exception as e:
            logger.error(f"요청 거부 실패: {str(e)}")
            return None

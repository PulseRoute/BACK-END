"""
Firebase 클라이언트
Firestore 데이터베이스 작업 처리
"""
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase Firestore 클라이언트"""
    
    _instance = None
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Firebase 초기화"""
        if self._initialized:
            return
        
        try:
            # Firebase credentials 파일 확인
            creds_path = settings.FIREBASE_CREDENTIALS_PATH
            if not os.path.exists(creds_path):
                logger.warning(f"Firebase credentials 파일을 찾을 수 없습니다: {creds_path}")
                self.db = None
                self._initialized = True
                return
            
            # Firebase 앱 초기화
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firebase 초기화 성공")
            self._initialized = True
        except Exception as e:
            logger.error(f"Firebase 초기화 실패: {str(e)}")
            self.db = None
            self._initialized = True
    
    def _check_db(self) -> bool:
        """데이터베이스 연결 확인"""
        if self.db is None:
            logger.error("Firebase 데이터베이스가 초기화되지 않았습니다")
            return False
        return True
    
    # ============= 사용자 관련 =============
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        사용자 생성
        
        Args:
            user_data: 사용자 정보
            
        Returns:
            생성된 문서 ID
        """
        if not self._check_db():
            raise Exception("데이터베이스 연결 실패")
        
        try:
            user_data["created_at"] = datetime.utcnow()
            doc_ref = self.db.collection("users").document()
            doc_ref.set(user_data)
            logger.info(f"사용자 생성 성공: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"사용자 생성 실패: {str(e)}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        이메일로 사용자 조회
        
        Args:
            email: 사용자 이메일
            
        Returns:
            사용자 정보 또는 None
        """
        if not self._check_db():
            return None
        
        try:
            query = self.db.collection("users").where("email", "==", email)
            docs = list(query.stream())
            
            if docs:
                user_data = docs[0].to_dict()
                user_data["id"] = docs[0].id
                logger.info(f"사용자 조회 성공: {email}")
                return user_data
            
            logger.info(f"사용자를 찾을 수 없습니다: {email}")
            return None
        except Exception as e:
            logger.error(f"사용자 조회 실패: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 사용자 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자 정보 또는 None
        """
        if not self._check_db():
            return None
        
        try:
            doc = self.db.collection("users").document(user_id).get()
            if doc.exists:
                user_data = doc.to_dict()
                user_data["id"] = doc.id
                return user_data
            return None
        except Exception as e:
            logger.error(f"사용자 조회 실패: {str(e)}")
            return None
    
    # ============= 환자 관련 =============
    
    def create_patient(self, patient_data: Dict[str, Any]) -> str:
        """
        환자 생성
        
        Args:
            patient_data: 환자 정보
            
        Returns:
            생성된 문서 ID
        """
        if not self._check_db():
            raise Exception("데이터베이스 연결 실패")
        
        try:
            patient_data["created_at"] = datetime.utcnow()
            doc_ref = self.db.collection("patients").document()
            doc_ref.set(patient_data)
            logger.info(f"환자 생성 성공: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"환자 생성 실패: {str(e)}")
            raise
    
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        환자 조회
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            환자 정보 또는 None
        """
        if not self._check_db():
            return None
        
        try:
            doc = self.db.collection("patients").document(patient_id).get()
            if doc.exists:
                patient_data = doc.to_dict()
                patient_data["id"] = doc.id
                return patient_data
            return None
        except Exception as e:
            logger.error(f"환자 조회 실패: {str(e)}")
            return None
    
    def get_patients_by_ems(self, ems_unit_id: str) -> List[Dict[str, Any]]:
        """
        EMS 유닛별 환자 목록 조회
        
        Args:
            ems_unit_id: EMS 유닛 ID
            
        Returns:
            환자 목록
        """
        if not self._check_db():
            return []
        
        try:
            query = self.db.collection("patients").where("ems_unit_id", "==", ems_unit_id)
            docs = list(query.stream())
            
            patients = []
            for doc in docs:
                patient_data = doc.to_dict()
                patient_data["id"] = doc.id
                patients.append(patient_data)
            
            return patients
        except Exception as e:
            logger.error(f"환자 목록 조회 실패: {str(e)}")
            return []
    
    def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> bool:
        """
        환자 정보 수정
        
        Args:
            patient_id: 환자 ID
            update_data: 수정할 정보
            
        Returns:
            성공 여부
        """
        if not self._check_db():
            return False
        
        try:
            self.db.collection("patients").document(patient_id).update(update_data)
            logger.info(f"환자 정보 수정 성공: {patient_id}")
            return True
        except Exception as e:
            logger.error(f"환자 정보 수정 실패: {str(e)}")
            return False
    
    # ============= 이송 요청 관련 =============
    
    def create_transfer_request(self, request_data: Dict[str, Any]) -> str:
        """
        이송 요청 생성
        
        Args:
            request_data: 요청 정보
            
        Returns:
            생성된 문서 ID
        """
        if not self._check_db():
            raise Exception("데이터베이스 연결 실패")
        
        try:
            request_data["created_at"] = datetime.utcnow()
            request_data["updated_at"] = datetime.utcnow()
            doc_ref = self.db.collection("transfer_requests").document()
            doc_ref.set(request_data)
            logger.info(f"이송 요청 생성 성공: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"이송 요청 생성 실패: {str(e)}")
            raise
    
    def get_transfer_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        이송 요청 조회
        
        Args:
            request_id: 요청 ID
            
        Returns:
            요청 정보 또는 None
        """
        if not self._check_db():
            return None
        
        try:
            doc = self.db.collection("transfer_requests").document(request_id).get()
            if doc.exists:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                return request_data
            return None
        except Exception as e:
            logger.error(f"이송 요청 조회 실패: {str(e)}")
            return None
    
    def get_pending_requests_for_hospital(self, hospital_id: str) -> List[Dict[str, Any]]:
        """
        병원의 대기중인 이송 요청 조회
        
        Args:
            hospital_id: 병원 ID
            
        Returns:
            요청 목록
        """
        if not self._check_db():
            return []
        
        try:
            query = self.db.collection("transfer_requests").where(
                "hospital_id", "==", hospital_id
            ).where("status", "==", "pending")
            docs = list(query.stream())
            
            requests = []
            for doc in docs:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                requests.append(request_data)
            
            return requests
        except Exception as e:
            logger.error(f"대기 요청 조회 실패: {str(e)}")
            return []
    
    def get_requests_for_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        환자의 모든 이송 요청 조회
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            요청 목록
        """
        if not self._check_db():
            return []
        
        try:
            query = self.db.collection("transfer_requests").where("patient_id", "==", patient_id)
            docs = list(query.stream())
            
            requests = []
            for doc in docs:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                requests.append(request_data)
            
            return requests
        except Exception as e:
            logger.error(f"환자 요청 조회 실패: {str(e)}")
            return []
    
    def update_transfer_request(self, request_id: str, update_data: Dict[str, Any]) -> bool:
        """
        이송 요청 수정
        
        Args:
            request_id: 요청 ID
            update_data: 수정할 정보
            
        Returns:
            성공 여부
        """
        if not self._check_db():
            return False
        
        try:
            update_data["updated_at"] = datetime.utcnow()
            self.db.collection("transfer_requests").document(request_id).update(update_data)
            logger.info(f"이송 요청 수정 성공: {request_id}")
            return True
        except Exception as e:
            logger.error(f"이송 요청 수정 실패: {str(e)}")
            return False
    
    # ============= 채팅 관련 =============
    
    def create_chat_room(self, room_data: Dict[str, Any]) -> str:
        """
        채팅방 생성
        
        Args:
            room_data: 채팅방 정보
            
        Returns:
            생성된 문서 ID
        """
        if not self._check_db():
            raise Exception("데이터베이스 연결 실패")
        
        try:
            room_data["created_at"] = datetime.utcnow()
            doc_ref = self.db.collection("chat_rooms").document()
            doc_ref.set(room_data)
            logger.info(f"채팅방 생성 성공: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"채팅방 생성 실패: {str(e)}")
            raise
    
    def get_chat_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        채팅방 조회
        
        Args:
            room_id: 채팅방 ID
            
        Returns:
            채팅방 정보 또는 None
        """
        if not self._check_db():
            return None
        
        try:
            doc = self.db.collection("chat_rooms").document(room_id).get()
            if doc.exists:
                room_data = doc.to_dict()
                room_data["id"] = doc.id
                return room_data
            return None
        except Exception as e:
            logger.error(f"채팅방 조회 실패: {str(e)}")
            return None
    
    def create_chat_message(self, message_data: Dict[str, Any]) -> str:
        """
        채팅 메시지 생성
        
        Args:
            message_data: 메시지 정보
            
        Returns:
            생성된 문서 ID
        """
        if not self._check_db():
            raise Exception("데이터베이스 연결 실패")
        
        try:
            message_data["timestamp"] = datetime.utcnow()
            doc_ref = self.db.collection("chat_messages").document()
            doc_ref.set(message_data)
            logger.info(f"채팅 메시지 생성 성공: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"채팅 메시지 생성 실패: {str(e)}")
            raise
    
    def get_chat_messages(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        채팅방 메시지 조회
        
        Args:
            room_id: 채팅방 ID
            limit: 조회할 메시지 수
            
        Returns:
            메시지 목록
        """
        if not self._check_db():
            return []
        
        try:
            query = self.db.collection("chat_messages").where(
                "room_id", "==", room_id
            ).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
            docs = list(query.stream())
            
            messages = []
            for doc in docs:
                message_data = doc.to_dict()
                message_data["id"] = doc.id
                messages.append(message_data)
            
            # 타임스탬프 순으로 정렬
            messages.sort(key=lambda x: x["timestamp"])
            return messages
        except Exception as e:
            logger.error(f"메시지 조회 실패: {str(e)}")
            return []
    
    # ============= 병원 관련 =============
    
    def get_hospitals_in_radius(self, latitude: float, longitude: float, radius_km: float) -> List[Dict[str, Any]]:
        """
        특정 위치 반경 내의 병원 조회
        Firestore는 지리적 쿼리를 네이티브로 지원하지 않으므로
        모든 병원을 조회 후 클라이언트에서 필터링
        
        Args:
            latitude: 위도
            longitude: 경도
            radius_km: 반경 (km)
            
        Returns:
            병원 목록
        """
        if not self._check_db():
            return []
        
        try:
            query = self.db.collection("users").where("type", "==", "hospital")
            docs = list(query.stream())
            
            hospitals = []
            for doc in docs:
                hospital_data = doc.to_dict()
                hospital_data["id"] = doc.id
                hospitals.append(hospital_data)
            
            return hospitals
        except Exception as e:
            logger.error(f"병원 조회 실패: {str(e)}")
            return []

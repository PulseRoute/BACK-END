"""
채팅 서비스
채팅방 및 메시지 관리
"""
from app.utils.firebase_client import FirebaseClient
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """채팅 서비스"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
    
    def get_user_chat_rooms(self, user_id: str) -> List[Dict[str, Any]]:
        """
        사용자의 채팅방 목록 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            채팅방 목록
        """
        try:
            # Firestore는 OR 쿼리를 기본으로 지원하지 않으므로
            # 두 개의 쿼리를 별도로 실행
            rooms_as_ems = []
            rooms_as_hospital = []
            
            if True:  # 모든 조회 시도
                # EMS로 참여한 채팅방
                try:
                    docs = list(
                        self.firebase_client.db.collection("chat_rooms")
                        .where("ems_unit_id", "==", user_id)
                        .stream()
                    )
                    for doc in docs:
                        room_data = doc.to_dict()
                        room_data["id"] = doc.id
                        rooms_as_ems.append(room_data)
                except:
                    pass
                
                # Hospital로 참여한 채팅방
                try:
                    docs = list(
                        self.firebase_client.db.collection("chat_rooms")
                        .where("hospital_id", "==", user_id)
                        .stream()
                    )
                    for doc in docs:
                        room_data = doc.to_dict()
                        room_data["id"] = doc.id
                        rooms_as_hospital.append(room_data)
                except:
                    pass
            
            rooms = rooms_as_ems + rooms_as_hospital
            logger.info(f"채팅방 목록 조회: {user_id} - {len(rooms)}개")
            return rooms
        except Exception as e:
            logger.error(f"채팅방 목록 조회 실패: {str(e)}")
            return []
    
    def get_chat_messages(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        채팅방 메시지 조회
        
        Args:
            room_id: 채팅방 ID
            limit: 조회할 메시지 수
            
        Returns:
            메시지 목록
        """
        try:
            messages = self.firebase_client.get_chat_messages(room_id, limit)
            logger.info(f"메시지 조회: {room_id} - {len(messages)}개")
            return messages
        except Exception as e:
            logger.error(f"메시지 조회 실패: {str(e)}")
            return []
    
    def create_message(
        self,
        room_id: str,
        sender_id: str,
        sender_type: str,
        message: str,
    ) -> Optional[Dict[str, Any]]:
        """
        메시지 생성
        
        Args:
            room_id: 채팅방 ID
            sender_id: 발신자 ID
            sender_type: 발신자 타입 ("ems" 또는 "hospital")
            message: 메시지 내용
            
        Returns:
            생성된 메시지 정보 또는 None
        """
        try:
            # 채팅방 확인
            room = self.firebase_client.get_chat_room(room_id)
            if not room:
                logger.warning(f"채팅방을 찾을 수 없습니다: {room_id}")
                return None
            
            # 사용자가 해당 채팅방에 참여하는지 확인
            if sender_type == "ems" and room.get("ems_unit_id") != sender_id:
                logger.warning(f"권한 없음: {room_id} - EMS {sender_id}")
                return None
            
            if sender_type == "hospital" and room.get("hospital_id") != sender_id:
                logger.warning(f"권한 없음: {room_id} - Hospital {sender_id}")
                return None
            
            # 메시지 생성
            message_data = {
                "room_id": room_id,
                "sender_id": sender_id,
                "sender_type": sender_type,
                "message": message,
                "is_read": False,
            }
            
            message_id = self.firebase_client.create_chat_message(message_data)
            logger.info(f"메시지 생성 성공: {message_id}")
            
            # 생성된 메시지 정보 반환
            created_message = self.firebase_client.get_chat_messages(room_id, 1)
            if created_message:
                return created_message[0]
            
            return None
        except Exception as e:
            logger.error(f"메시지 생성 실패: {str(e)}")
            return None

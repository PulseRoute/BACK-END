"""
채팅 관련 스키마
"""
from pydantic import BaseModel
from typing import List
from datetime import datetime


class ChatMessageSchema(BaseModel):
    """채팅 메시지"""
    id: str
    room_id: str
    sender_id: str
    sender_type: str
    message: str
    timestamp: datetime
    is_read: bool = False
    
    class Config:
        from_attributes = True


class ChatRoomSchema(BaseModel):
    """채팅 룸"""
    id: str
    patient_id: str
    ems_unit_id: str
    hospital_id: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ChatRoomDetailSchema(ChatRoomSchema):
    """채팅 룸 상세"""
    latest_messages: List[ChatMessageSchema] = []


class ChatMessageCreateSchema(BaseModel):
    """채팅 메시지 생성"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "환자가 도착했습니다",
            }
        }

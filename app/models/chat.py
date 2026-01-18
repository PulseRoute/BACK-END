"""
채팅 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRoomBase(BaseModel):
    """채팅룸 기본 모델"""
    patient_id: str
    ems_unit_id: str
    hospital_id: str


class ChatRoomCreate(ChatRoomBase):
    """채팅룸 생성 모델"""
    pass


class ChatRoomInDB(ChatRoomBase):
    """데이터베이스 저장 모델"""
    id: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class ChatRoom(ChatRoomBase):
    """응답 모델"""
    id: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    """채팅 메시지 기본 모델"""
    room_id: str
    sender_id: str
    sender_type: str  # "ems" 또는 "hospital"
    message: str


class ChatMessageCreate(ChatMessageBase):
    """채팅 메시지 생성 모델"""
    pass


class ChatMessageInDB(ChatMessageBase):
    """데이터베이스 저장 모델"""
    id: str
    timestamp: datetime
    is_read: bool = False
    
    class Config:
        from_attributes = True


class ChatMessage(ChatMessageBase):
    """응답 모델"""
    id: str
    timestamp: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

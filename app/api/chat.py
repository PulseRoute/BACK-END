"""
채팅 API 라우터
WebSocket 및 HTTP 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from app.schemas.chat import ChatMessageSchema, ChatRoomDetailSchema, ChatMessageCreateSchema
from app.services.chat_service import ChatService
from app.dependencies import get_current_user
from typing import Dict, Any, List, Set
from datetime import datetime
import logging
import json

router = APIRouter()
chat_service = ChatService()
logger = logging.getLogger(__name__)

# WebSocket 연결 관리
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, room_id: str, websocket: WebSocket):
        """연결 추가"""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        logger.info(f"WebSocket 연결: {room_id} - 총 {len(self.active_connections[room_id])}명")
    
    def disconnect(self, room_id: str, websocket: WebSocket):
        """연결 제거"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            logger.info(f"WebSocket 해제: {room_id} - 총 {len(self.active_connections.get(room_id, set()))}명")
    
    async def broadcast(self, room_id: str, message: dict):
        """메시지 브로드캐스트"""
        if room_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"메시지 전송 실패: {str(e)}")
                    disconnected.add(connection)
            
            # 연결 끊긴 클라이언트 제거
            self.active_connections[room_id] -= disconnected


manager = ConnectionManager()


@router.get("/rooms", response_model=List[ChatRoomDetailSchema])
async def get_chat_rooms(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    사용자의 채팅방 목록 조회
    
    반환:
    - 채팅방 리스트
    """
    try:
        rooms = chat_service.get_user_chat_rooms(current_user["user_id"])
        logger.info(f"채팅방 목록 조회: {current_user['user_id']} - {len(rooms)}개")
        return rooms
    except Exception as e:
        logger.error(f"채팅방 목록 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅방 조회 중 오류가 발생했습니다",
        )


@router.get("/rooms/{room_id}/messages", response_model=List[ChatMessageSchema])
async def get_messages(
    room_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    채팅방 메시지 히스토리 조회
    
    - **room_id**: 채팅방 ID
    - **limit**: 조회할 메시지 수 (기본값: 50)
    
    반환:
    - 메시지 리스트
    """
    try:
        messages = chat_service.get_chat_messages(room_id, limit)
        logger.info(f"메시지 히스토리 조회: {room_id} - {len(messages)}개")
        return messages
    except Exception as e:
        logger.error(f"메시지 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 조회 중 오류가 발생했습니다",
        )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    실시간 채팅 WebSocket
    
    - **room_id**: 채팅방 ID
    
    메시지 형식:
    {
        "type": "message",
        "sender_id": "user_id",
        "sender_type": "ems|hospital",
        "message": "메시지 내용"
    }
    """
    try:
        # 연결
        await manager.connect(room_id, websocket)
        
        # 연결 메시지 브로드캐스트
        await manager.broadcast(room_id, {
            "type": "system",
            "message": "사용자가 채팅방에 입장했습니다",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # 메시지 수신 루프
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # 메시지 생성
                created_message = chat_service.create_message(
                    room_id=room_id,
                    sender_id=message_data.get("sender_id"),
                    sender_type=message_data.get("sender_type"),
                    message=message_data.get("message"),
                )
                
                if created_message:
                    # 다른 클라이언트에게 브로드캐스트
                    await manager.broadcast(room_id, {
                        "type": "message",
                        "id": created_message.get("id"),
                        "sender_id": created_message.get("sender_id"),
                        "sender_type": created_message.get("sender_type"),
                        "message": created_message.get("message"),
                        "timestamp": created_message.get("timestamp").isoformat() if created_message.get("timestamp") else None,
                    })
                    
                    logger.info(f"메시지 브로드캐스트: {room_id}")
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "유효하지 않은 메시지 형식입니다",
                })
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        
        # 퇴장 메시지 브로드캐스트
        await manager.broadcast(room_id, {
            "type": "system",
            "message": "사용자가 채팅방을 나갔습니다",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        logger.info(f"WebSocket 연결 해제: {room_id}")
    except Exception as e:
        logger.error(f"WebSocket 에러: {str(e)}")
        try:
            await websocket.close(code=1000)
        except:
            pass
        finally:
            manager.disconnect(room_id, websocket)

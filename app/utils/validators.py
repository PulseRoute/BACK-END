"""
입력 검증 유틸리티
"""
from typing import Tuple
import re
import math
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    이메일 주소 유효성 검증
    
    Args:
        email: 이메일 주소
        
    Returns:
        유효 여부
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> Tuple[bool, str]:
    """
    비밀번호 유효성 검증
    최소 8자, 숫자, 특문 포함
    
    Args:
        password: 비밀번호
        
    Returns:
        (유효 여부, 메시지)
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"
    
    if not re.search(r"\d", password):
        return False, "비밀번호에 숫자가 포함되어야 합니다"
    
    return True, "유효한 비밀번호입니다"


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    좌표 유효성 검증
    
    Args:
        latitude: 위도 (-90 ~ 90)
        longitude: 경도 (-180 ~ 180)
        
    Returns:
        유효 여부
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 지점 사이의 거리 계산 (Haversine 공식)
    
    Args:
        lat1, lon1: 첫 번째 지점
        lat2, lon2: 두 번째 지점
        
    Returns:
        거리 (km)
    """
    # 지구 반지름 (km)
    R = 6371.0
    
    # 각도를 라디안으로 변환
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 차이 계산
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine 공식
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def validate_patient_data(name: str, age: int, gender: str) -> Tuple[bool, str]:
    """
    환자 정보 유효성 검증
    
    Args:
        name: 이름
        age: 나이
        gender: 성별
        
    Returns:
        (유효 여부, 메시지)
    """
    if not name or len(name.strip()) == 0:
        return False, "환자 이름이 필요합니다"
    
    if age < 0 or age > 150:
        return False, "유효하지 않은 나이입니다"
    
    if gender not in ["M", "F"]:
        return False, "성별은 M 또는 F여야 합니다"
    
    return True, "유효한 환자 정보입니다"


def validate_severity_code(severity_code: str) -> bool:
    """
    KTAS 중증도 코드 유효성 검증
    
    Args:
        severity_code: 중증도 코드
        
    Returns:
        유효 여부
    """
    valid_codes = ["KTAS_1", "KTAS_2", "KTAS_3", "KTAS_4", "KTAS_5"]
    return severity_code in valid_codes

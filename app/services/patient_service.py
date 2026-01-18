"""
환자 서비스
환자 관리, ML 매칭 등
"""
from app.utils.firebase_client import FirebaseClient
from app.utils.validators import calculate_distance, validate_patient_data
from app.config import settings
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """환자 서비스"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
    
    async def register_patient(self, ems_unit_id: str, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        환자 등록 및 자동 병원 매칭
        
        Args:
            ems_unit_id: EMS 유닛 ID
            patient_data: 환자 정보
            
        Returns:
            환자 정보 또는 None
        """
        try:
            # 환자 정보 검증
            is_valid, message = validate_patient_data(
                patient_data["name"],
                patient_data["age"],
                patient_data["gender"],
            )
            if not is_valid:
                logger.warning(f"환자 정보 검증 실패: {message}")
                return None
            
            # 환자 생성
            patient_doc_data = {
                "ems_unit_id": ems_unit_id,
                "name": patient_data["name"],
                "age": patient_data["age"],
                "gender": patient_data["gender"],
                "disease_code": patient_data["disease_code"],
                "severity_code": patient_data["severity_code"],
                "location": patient_data["location"],
                "vital_signs": patient_data.get("vital_signs"),
                "status": "searching",
            }
            
            patient_id = self.firebase_client.create_patient(patient_doc_data)
            
            # 반경 내 병원 검색
            hospitals = self.firebase_client.get_hospitals_in_radius(
                patient_data["location"]["latitude"],
                patient_data["location"]["longitude"],
                settings.MAX_HOSPITAL_SEARCH_RADIUS_KM,
            )
            
            # ML 서버로 매칭 요청
            matched_hospitals = await self._get_ml_matches(
                patient_id,
                patient_data,
                hospitals,
            )
            
            # 자동으로 이송 요청 생성
            await self._create_transfer_requests(
                patient_id,
                ems_unit_id,
                matched_hospitals,
            )
            
            # 환자 상태 업데이트
            self.firebase_client.update_patient(patient_id, {"status": "matched"})
            
            logger.info(f"환자 등록 성공: {patient_id}")
            
            # 생성된 환자 정보 반환
            patient = self.firebase_client.get_patient(patient_id)
            return patient
        except Exception as e:
            logger.error(f"환자 등록 실패: {str(e)}")
            return None
    
    async def _get_ml_matches(
        self,
        patient_id: str,
        patient_data: Dict[str, Any],
        hospitals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        ML 서버에서 매칭된 병원 목록 조회
        
        Args:
            patient_id: 환자 ID
            patient_data: 환자 정보
            hospitals: 병원 목록
            
        Returns:
            매칭된 병원 리스트
        """
        try:
            # ML 서버 요청 데이터 구성
            ml_request = {
                "patient_id": patient_id,
                "location": patient_data["location"],
                "disease_code": patient_data["disease_code"],
                "severity_code": patient_data["severity_code"],
                "hospitals": [
                    {
                        "hospital_id": h["id"],
                        "name": h["name"],
                        "latitude": h.get("latitude", 0),
                        "longitude": h.get("longitude", 0),
                        "specialty": h.get("specialty", []),
                        "available_beds": h.get("available_beds", 0),
                    }
                    for h in hospitals
                ],
            }
            
            # ML 서버 호출
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ML_SERVER_URL}/match",
                    json=ml_request,
                    timeout=settings.ML_SERVER_TIMEOUT,
                )
                
                if response.status_code == 200:
                    ml_result = response.json()
                    logger.info(f"ML 매칭 성공: {patient_id}")
                    
                    # ML 점수와 거리 정보 추가
                    matches = []
                    for match in ml_result.get("matches", []):
                        hospital = next(
                            (h for h in hospitals if h["id"] == match["hospital_id"]),
                            None,
                        )
                        if hospital:
                            match["hospital_info"] = hospital
                            matches.append(match)
                    
                    return matches
                else:
                    logger.warning(f"ML 서버 오류: {response.status_code}")
                    return self._fallback_distance_based_matching(patient_data["location"], hospitals)
        except Exception as e:
            logger.error(f"ML 서버 연동 실패: {str(e)}")
            # Fallback: 거리 기반 매칭
            return self._fallback_distance_based_matching(patient_data["location"], hospitals)
    
    def _fallback_distance_based_matching(
        self,
        location: Dict[str, float],
        hospitals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Fallback: 거리 기반 매칭
        
        Args:
            location: 환자 위치
            hospitals: 병원 목록
            
        Returns:
            거리순 정렬된 병원 리스트
        """
        matches = []
        
        for hospital in hospitals:
            distance = calculate_distance(
                location["latitude"],
                location["longitude"],
                hospital.get("latitude", 0),
                hospital.get("longitude", 0),
            )
            
            matches.append({
                "hospital_id": hospital["id"],
                "hospital_info": hospital,
                "ml_score": 0.5,  # 기본 점수
                "distance_km": round(distance, 2),
                "estimated_time_minutes": int(distance * 2),  # 평균 2분/km 추정
            })
        
        # 거리순 정렬
        matches.sort(key=lambda x: x["distance_km"])
        
        logger.info(f"거리 기반 매칭 사용: {len(matches)}개 병원")
        return matches
    
    async def _create_transfer_requests(
        self,
        patient_id: str,
        ems_unit_id: str,
        matched_hospitals: List[Dict[str, Any]],
    ) -> None:
        """
        이송 요청 자동 생성
        
        Args:
            patient_id: 환자 ID
            ems_unit_id: EMS 유닛 ID
            matched_hospitals: 매칭된 병원 리스트
        """
        try:
            for match in matched_hospitals[:10]:  # 최대 10개 병원까지만
                request_data = {
                    "patient_id": patient_id,
                    "ems_unit_id": ems_unit_id,
                    "hospital_id": match["hospital_id"],
                    "status": "pending",
                    "ml_score": match.get("ml_score", 0.5),
                    "distance_km": match.get("distance_km", 0),
                    "estimated_time_minutes": match.get("estimated_time_minutes", 0),
                }
                
                self.firebase_client.create_transfer_request(request_data)
            
            logger.info(f"이송 요청 생성 완료: {patient_id} - {len(matched_hospitals)}개")
        except Exception as e:
            logger.error(f"이송 요청 생성 실패: {str(e)}")
    
    def get_patient_requests(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        환자의 요청 상태 조회
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            환자의 요청 정보 또는 None
        """
        try:
            patient = self.firebase_client.get_patient(patient_id)
            
            if not patient:
                return None
            
            requests = self.firebase_client.get_requests_for_patient(patient_id)
            
            return {
                "patient_id": patient_id,
                "patient_name": patient["name"],
                "status": patient["status"],
                "requests": requests,
            }
        except Exception as e:
            logger.error(f"환자 요청 조회 실패: {str(e)}")
            return None

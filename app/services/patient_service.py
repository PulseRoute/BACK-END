"""
환자 서비스
환자 관리, ML 매칭 등
"""
from app.utils.firebase_client import FirebaseClient
from app.utils.validators import validate_patient_data
from app.config import settings
import httpx
from typing import Dict, List, Any, Optional
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

            # ML 서버로 매칭 요청 (ML 서버가 병원 검색/거리 계산 수행)
            matched_hospitals = await self._get_ml_matches(patient_data)

            # ML 실패 시: status는 searching 유지
            # ML 성공 시: status를 matched로 변경 (이송 요청은 별도 API에서 생성)
            if not matched_hospitals:
                logger.warning(f"ML 매칭 실패, 환자 등록만 완료: {patient_id}")
            else:
                # 환자 상태 업데이트 (추천 병원 있음)
                self.firebase_client.update_patient(patient_id, {"status": "matched"})

            logger.info(f"환자 등록 성공: {patient_id}")

            # 생성된 환자 정보 반환 (매칭된 병원 목록 포함)
            patient = self.firebase_client.get_patient(patient_id)

            # 매칭된 병원 정보 추가
            if matched_hospitals:
                patient["matched_hospitals"] = [
                    {
                        "hospital_id": h.get("hospital_id"),
                        "name": h.get("name", ""),
                        "address": h.get("address", ""),
                        "ml_score": h.get("ml_score"),
                        "distance_km": h.get("distance_km"),
                        "estimated_time_minutes": h.get("estimated_time_minutes"),
                        "recommendation_reason": h.get("recommendation_reason", ""),
                        "total_beds": h.get("total_beds"),
                        "has_trauma_center": h.get("has_trauma_center"),
                    }
                    for h in matched_hospitals
                ]

            return patient
        except Exception as e:
            logger.error(f"환자 등록 실패: {str(e)}")
            return None
    
    async def _get_ml_matches(
        self,
        patient_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        ML 서버에서 매칭된 병원 목록 조회

        Args:
            patient_data: 환자 정보

        Returns:
            매칭된 병원 리스트
        """
        try:
            # ML 서버 요청 데이터 구성 (신규 API 형식)
            ml_request = {
                "name": patient_data["name"],
                "age": patient_data["age"],
                "gender": patient_data["gender"],
                "disease_code": patient_data["disease_code"],
                "severity_code": patient_data["severity_code"],
                "location": patient_data["location"],
            }

            # ML 서버 호출 (신규 엔드포인트)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ML_SERVER_URL}/api/predict/rank",
                    json=ml_request,
                    timeout=settings.ML_SERVER_TIMEOUT,
                )

                if response.status_code == 200:
                    ml_result = response.json()
                    logger.info("ML 매칭 성공")

                    # ranked_hospitals 배열에서 병원 정보 추출
                    matches = []
                    for hospital in ml_result.get("ranked_hospitals", []):
                        matches.append({
                            "hospital_id": hospital.get("facid"),
                            "name": hospital.get("name"),
                            "address": hospital.get("address"),
                            "ml_score": hospital.get("final_score", 0),
                            "distance_km": hospital.get("distance_km", 0),
                            "estimated_time_minutes": int(hospital.get("duration_minutes", 0)),
                            "recommendation_reason": hospital.get("recommendation_reason"),
                            "total_beds": hospital.get("total_beds"),
                            "has_trauma_center": hospital.get("has_trauma_center"),
                            "hospital_info": hospital,
                        })

                    return matches
                else:
                    logger.warning(f"ML 서버 오류: {response.status_code}")
                    return self._fallback_distance_based_matching()
        except Exception as e:
            logger.error(f"ML 서버 연동 실패: {str(e)}")
            return self._fallback_distance_based_matching()
    
    def _fallback_distance_based_matching(self) -> List[Dict[str, Any]]:
        """
        Fallback: ML 실패 시 빈 배열 반환
        (Firebase에 병원 정보가 없으므로 거리 기반 매칭 불가)

        Returns:
            빈 배열
        """
        logger.warning("ML 서버 실패, 병원 매칭 불가 (fallback 사용 불가)")
        return []
    
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
                    "hospital_name": match.get("name", ""),
                    "hospital_address": match.get("address", ""),
                    "status": "pending",
                    "ml_score": match.get("ml_score", 0),
                    "distance_km": match.get("distance_km", 0),
                    "estimated_time_minutes": match.get("estimated_time_minutes", 0),
                    "recommendation_reason": match.get("recommendation_reason", ""),
                    "total_beds": match.get("total_beds"),
                    "has_trauma_center": match.get("has_trauma_center"),
                }
                
                self.firebase_client.create_transfer_request(request_data)
            
            logger.info(f"이송 요청 생성 완료: {patient_id} - {len(matched_hospitals)}개")
        except Exception as e:
            logger.error(f"이송 요청 생성 실패: {str(e)}")
    
    async def retry_match(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        ML 매칭 재시도 (searching 상태인 환자에 대해)

        Args:
            patient_id: 환자 ID

        Returns:
            성공 시 환자 정보, 실패 시 None
        """
        try:
            patient = self.firebase_client.get_patient(patient_id)

            if not patient:
                logger.warning(f"환자를 찾을 수 없음: {patient_id}")
                return None

            if patient.get("status") != "searching":
                logger.warning(f"재매칭 불가 상태: {patient_id}, status={patient.get('status')}")
                return None

            # 환자 정보로 ML 매칭 재시도
            patient_data = {
                "name": patient["name"],
                "age": patient["age"],
                "gender": patient["gender"],
                "disease_code": patient["disease_code"],
                "severity_code": patient["severity_code"],
                "location": patient["location"],
            }

            matched_hospitals = await self._get_ml_matches(patient_data)

            if not matched_hospitals:
                logger.warning(f"ML 재매칭 실패: {patient_id}")
                return None

            # 환자 상태 업데이트
            self.firebase_client.update_patient(patient_id, {"status": "matched"})

            logger.info(f"ML 재매칭 성공: {patient_id}")

            # 환자 정보 반환 (매칭된 병원 목록 포함)
            updated_patient = self.firebase_client.get_patient(patient_id)
            updated_patient["matched_hospitals"] = [
                {
                    "hospital_id": h.get("hospital_id"),
                    "name": h.get("name", ""),
                    "address": h.get("address", ""),
                    "ml_score": h.get("ml_score"),
                    "distance_km": h.get("distance_km"),
                    "estimated_time_minutes": h.get("estimated_time_minutes"),
                    "recommendation_reason": h.get("recommendation_reason", ""),
                    "total_beds": h.get("total_beds"),
                    "has_trauma_center": h.get("has_trauma_center"),
                }
                for h in matched_hospitals
            ]
            return updated_patient

        except Exception as e:
            logger.error(f"ML 재매칭 중 오류: {str(e)}")
            return None

    def get_active_patients(self, ems_unit_id: str) -> List[Dict[str, Any]]:
        """
        EMS 유닛의 활성 환자 목록 조회 (해결된 환자 제외)

        Args:
            ems_unit_id: EMS 유닛 ID

        Returns:
            활성 환자 목록 (status가 transferred가 아닌 환자)
        """
        try:
            patients = self.firebase_client.get_patients_by_ems(ems_unit_id)

            # transferred 상태 제외
            active_patients = [
                p for p in patients if p.get("status") != "transferred"
            ]

            # 최신순 정렬
            active_patients.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            logger.info(f"활성 환자 목록 조회: {ems_unit_id}, {len(active_patients)}명")
            return active_patients
        except Exception as e:
            logger.error(f"활성 환자 목록 조회 실패: {str(e)}")
            return []

    def complete_transfer(self, patient_id: str, ems_unit_id: str) -> Optional[Dict[str, Any]]:
        """
        환자 이송 완료 처리

        Args:
            patient_id: 환자 ID
            ems_unit_id: EMS 유닛 ID (권한 확인용)

        Returns:
            업데이트된 환자 정보 또는 None
        """
        try:
            patient = self.firebase_client.get_patient(patient_id)

            if not patient:
                logger.warning(f"환자를 찾을 수 없음: {patient_id}")
                return None

            # 권한 확인: 본인이 등록한 환자만 완료 처리 가능
            if patient.get("ems_unit_id") != ems_unit_id:
                logger.warning(f"권한 없음: {patient_id}, {ems_unit_id}")
                return None

            # 이미 완료된 환자인지 확인
            if patient.get("status") == "transferred":
                logger.warning(f"이미 이송 완료된 환자: {patient_id}")
                return patient

            # 상태 업데이트
            self.firebase_client.update_patient(patient_id, {"status": "transferred"})

            logger.info(f"환자 이송 완료: {patient_id}")
            return self.firebase_client.get_patient(patient_id)
        except Exception as e:
            logger.error(f"이송 완료 처리 실패: {str(e)}")
            return None

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

    def create_transfer_request(
        self,
        patient_id: str,
        ems_unit_id: str,
        hospital_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        특정 병원에 이송 요청 생성

        Args:
            patient_id: 환자 ID
            ems_unit_id: EMS 유닛 ID (권한 확인용)
            hospital_data: 병원 정보 (hospital_id, hospital_name 등)

        Returns:
            생성된 이송 요청 정보 또는 None
        """
        try:
            # 환자 확인
            patient = self.firebase_client.get_patient(patient_id)
            if not patient:
                logger.warning(f"환자를 찾을 수 없음: {patient_id}")
                return None

            # 권한 확인
            if patient.get("ems_unit_id") != ems_unit_id:
                logger.warning(f"권한 없음: {patient_id}, {ems_unit_id}")
                return None

            # 이미 이송 완료된 환자인지 확인
            if patient.get("status") == "transferred":
                logger.warning(f"이미 이송 완료된 환자: {patient_id}")
                return None

            # 이송 요청 생성
            # [시연용] 모든 요청을 hosp01로 전달
            demo_hospital_id = "hosp01"

            request_data = {
                "patient_id": patient_id,
                "ems_unit_id": ems_unit_id,
                "hospital_id": demo_hospital_id,  # 시연용: 항상 hosp01로 전달
                "hospital_name": hospital_data.get("hospital_name", ""),
                "hospital_address": hospital_data.get("hospital_address", ""),
                "status": "pending",
                "ml_score": hospital_data.get("ml_score", 0),
                "distance_km": hospital_data.get("distance_km", 0),
                "estimated_time_minutes": hospital_data.get("estimated_time_minutes", 0),
                "recommendation_reason": hospital_data.get("recommendation_reason", ""),
                "total_beds": hospital_data.get("total_beds"),
                "has_trauma_center": hospital_data.get("has_trauma_center"),
            }

            request_id = self.firebase_client.create_transfer_request(request_data)

            # 환자 상태 업데이트 (요청 중)
            self.firebase_client.update_patient(patient_id, {"status": "requesting"})

            logger.info(f"이송 요청 생성 성공: {patient_id} -> {hospital_data['hospital_id']}")

            # 생성된 요청 정보 반환
            return self.firebase_client.get_transfer_request(request_id)
        except Exception as e:
            logger.error(f"이송 요청 생성 실패: {str(e)}")
            return None

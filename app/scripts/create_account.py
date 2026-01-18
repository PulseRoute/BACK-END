"""
계정 생성 스크립트
CLI를 통해 EMS 또는 병원 계정을 생성
"""
import argparse
import sys
import logging
from app.utils.firebase_client import FirebaseClient
from app.services.auth_service import AuthService
from app.utils.validators import validate_email, validate_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_account(email: str, password: str, user_type: str, name: str) -> bool:
    """
    사용자 계정 생성
    
    Args:
        email: 이메일
        password: 비밀번호
        user_type: 사용자 타입 (ems 또는 hospital)
        name: 사용자 이름
        
    Returns:
        성공 여부
    """
    try:
        # 입력 검증
        if not validate_email(email):
            logger.error("유효하지 않은 이메일 주소입니다")
            return False
        
        is_valid, message = validate_password(password)
        if not is_valid:
            logger.error(f"비밀번호 검증 실패: {message}")
            return False
        
        if user_type not in ["ems", "hospital"]:
            logger.error("사용자 타입은 'ems' 또는 'hospital'이어야 합니다")
            return False
        
        if not name or len(name.strip()) == 0:
            logger.error("사용자 이름이 필요합니다")
            return False
        
        # Firebase 클라이언트 초기화
        firebase_client = FirebaseClient()
        
        if not firebase_client._check_db():
            logger.error("Firebase 데이터베이스 연결에 실패했습니다")
            logger.info("firebase-credentials.json 파일을 확인하세요")
            return False
        
        # 기존 사용자 확인
        existing_user = firebase_client.get_user_by_email(email)
        if existing_user:
            logger.error(f"이미 존재하는 이메일입니다: {email}")
            return False
        
        # 비밀번호 해싱
        auth_service = AuthService()
        password_hash = auth_service.hash_password(password)
        
        # 사용자 생성
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "type": user_type,
            "name": name,
        }
        
        user_id = firebase_client.create_user(user_data)
        
        logger.info(f"계정 생성 성공!")
        logger.info(f"  사용자 ID: {user_id}")
        logger.info(f"  이메일: {email}")
        logger.info(f"  타입: {user_type}")
        logger.info(f"  이름: {name}")
        
        return True
    except Exception as e:
        logger.error(f"계정 생성 중 오류: {str(e)}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="PulseRoute 백엔드 계정 생성 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # EMS 계정 생성
  python -m app.scripts.create_account \\
    --email ems01@example.com \\
    --password securepass123 \\
    --type ems \\
    --name "Seoul EMS Unit 1"
  
  # 병원 계정 생성
  python -m app.scripts.create_account \\
    --email hospital01@example.com \\
    --password securepass123 \\
    --type hospital \\
    --name "Seoul Central Hospital"
        """,
    )
    
    parser.add_argument(
        "--email",
        required=True,
        help="사용자 이메일",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="사용자 비밀번호 (최소 8자, 숫자 포함)",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["ems", "hospital"],
        help="사용자 타입",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="사용자 이름",
    )
    
    args = parser.parse_args()
    
    # 계정 생성
    success = create_account(
        args.email,
        args.password,
        args.type,
        args.name,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

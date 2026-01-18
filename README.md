# PulseRoute - 응급환자 이송 매칭 시스템 API

응급환자를 병원에 이송하기 위한 매칭 시스템의 백엔드 API입니다. FastAPI, JWT, Firebase를 사용하여 구축되었습니다.

## 프로젝트 개요

PulseRoute는 다음과 같은 기능을 제공합니다:

- **JWT 기반 인증**: EMS(구급대)와 Hospital(병원) 사용자 구분
- **환자 관리**: 환자 등록 및 자동 병원 매칭
- **병원 요청 관리**: 이송 요청 수락/거부 및 상태 추적
- **실시간 채팅**: WebSocket 기반 EMS와 병원 간 실시간 통신
- **이송 히스토리**: 완료된 이송 기록 및 타임라인 조회

## 기술 스택

- **Framework**: FastAPI 0.109.0
- **인증**: JWT (python-jose)
- **데이터베이스**: Firebase Firestore
- **비밀번호 암호화**: bcrypt
- **실시간 통신**: WebSocket
- **HTTP 클라이언트**: httpx
- **Python**: 3.10+

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                  # FastAPI 메인 애플리케이션
│   ├── config.py                # 설정 관리
│   ├── dependencies.py          # 의존성 주입
│   │
│   ├── models/                  # Pydantic 모델
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── hospital.py
│   │   ├── transfer_request.py
│   │   └── chat.py
│   │
│   ├── schemas/                 # API 스키마
│   │   ├── auth.py
│   │   ├── patient.py
│   │   ├── hospital.py
│   │   ├── request.py
│   │   └── chat.py
│   │
│   ├── api/                     # API 라우터
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── hospitals.py
│   │   ├── requests.py
│   │   ├── history.py
│   │   └── chat.py
│   │
│   ├── services/                # 비즈니스 로직
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── hospital_service.py
│   │   └── chat_service.py
│   │
│   ├── utils/                   # 유틸리티
│   │   ├── jwt_handler.py
│   │   ├── firebase_client.py
│   │   └── validators.py
│   │
│   └── scripts/
│       └── create_account.py    # 계정 생성 스크립트
│
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

## 설치 및 실행

### 1. 사전 요구사항

- Python 3.10 이상
- Firebase 프로젝트 설정 및 Firestore 데이터베이스 생성
- Firebase 서비스 계정 키 파일

### 2. 프로젝트 셋업

```bash
# 저장소 클론
cd BACK-END

# 가상 환경 생성 및 활성화
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
```

### 3. Firebase 설정

```bash
# Firebase 콘솔에서 다운로드한 서비스 계정 키를 프로젝트 루트에 배치
# firebase-credentials.json
```

### 4. .env 파일 수정

```bash
# .env 파일 수정
nano .env

# 다음 항목 입력:
JWT_SECRET_KEY=your-secret-key-here  # 안전한 시크릿 키 입력
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
ML_SERVER_URL=http://ml-server:8000  # ML 서버 주소
```

### 5. 개발 서버 실행

```bash
# 자동 리로드 활성화로 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

서버는 `http://localhost:8000`에서 실행됩니다.

### API 문서 접근

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 계정 생성

```bash
# EMS 계정 생성
python -m app.scripts.create_account \
  --email ems01@example.com \
  --password securepass123 \
  --type ems \
  --name "Seoul EMS Unit 1"

# 병원 계정 생성
python -m app.scripts.create_account \
  --email hospital01@example.com \
  --password securepass123 \
  --type hospital \
  --name "Seoul Central Hospital"
```

## API 엔드포인트

### 인증 (Authentication)

#### 로그인
```
POST /api/auth/login
```

**요청:**
```json
{
  "email": "ems01@example.com",
  "password": "securepass123"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "user_123",
  "user_type": "ems",
  "user_name": "Seoul EMS Unit 1"
}
```

### 환자 관리 (Patients) - EMS 전용

#### 환자 등록 및 자동 매칭
```
POST /api/patients
```

**요청:**
```json
{
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "disease_code": "I21.0",
  "severity_code": "KTAS_1",
  "location": {
    "latitude": 37.5665,
    "longitude": 126.9780
  },
  "vital_signs": {
    "blood_pressure": "120/80",
    "pulse": 75,
    "temperature": 36.5
  }
}
```

**응답:**
```json
{
  "id": "patient_123",
  "ems_unit_id": "ems_unit_1",
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "disease_code": "I21.0",
  "severity_code": "KTAS_1",
  "location": {
    "latitude": 37.5665,
    "longitude": 126.9780
  },
  "status": "matched",
  "created_at": "2026-01-18T10:30:00"
}
```

#### 환자의 요청 상태 조회
```
GET /api/patients/{patient_id}/requests
```

**응답:**
```json
{
  "patient_id": "patient_123",
  "patient_name": "홍길동",
  "status": "matched",
  "requests": [
    {
      "id": "request_1",
      "patient_id": "patient_123",
      "ems_unit_id": "ems_unit_1",
      "hospital_id": "hospital_1",
      "status": "pending",
      "ml_score": 0.95,
      "distance_km": 5.2,
      "estimated_time_minutes": 15,
      "created_at": "2026-01-18T10:30:00",
      "updated_at": "2026-01-18T10:30:00"
    }
  ]
}
```

### 병원 요청 관리 (Hospital) - Hospital 전용

#### 대기중인 요청 목록
```
GET /api/hospitals/requests/pending
```

**응답:**
```json
[
  {
    "id": "request_1",
    "patient_id": "patient_123",
    "ems_unit_id": "ems_unit_1",
    "hospital_id": "hospital_1",
    "status": "pending",
    "ml_score": 0.95,
    "distance_km": 5.2,
    "estimated_time_minutes": 15,
    "created_at": "2026-01-18T10:30:00",
    "updated_at": "2026-01-18T10:30:00"
  }
]
```

#### 이송 요청 수락
```
POST /api/requests/{request_id}/accept
```

**응답:**
```json
{
  "id": "request_1",
  "status": "accepted",
  "chat_room_id": "chat_room_123",
  "updated_at": "2026-01-18T10:35:00"
}
```

#### 이송 요청 거부
```
POST /api/requests/{request_id}/reject
```

**요청:**
```json
{
  "status": "rejected",
  "rejection_reason": "병상 부족"
}
```

### 히스토리 (History)

#### 이송 기록 조회
```
GET /api/history?days=30&severity_code=KTAS_1&page=1&limit=20
```

**쿼리 파라미터:**
- `days`: 조회 기간 (기본값: 30일)
- `severity_code`: 중증도 필터링 (선택사항)
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20)

**응답:**
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "records": [
    {
      "id": "request_1",
      "patient_id": "patient_123",
      "status": "accepted",
      "created_at": "2026-01-18T10:30:00"
    }
  ]
}
```

#### 환자 타임라인 조회
```
GET /api/history/{patient_id}/timeline
```

**응답:**
```json
{
  "patient_id": "patient_123",
  "patient_name": "홍길동",
  "timeline": [
    {
      "event": "환자 등록",
      "timestamp": "2026-01-18T10:30:00",
      "status": "completed",
      "description": "홍길동 (45세) 환자 등록"
    },
    {
      "event": "요청 대기",
      "timestamp": "2026-01-18T10:30:00",
      "status": "pending",
      "description": "병원에 이송 요청 대기 중"
    },
    {
      "event": "요청 수락",
      "timestamp": "2026-01-18T10:35:00",
      "status": "completed",
      "description": "병원에서 요청 수락"
    }
  ]
}
```

### 채팅 (Chat)

#### 채팅방 목록
```
GET /api/chat/rooms
```

**응답:**
```json
[
  {
    "id": "room_123",
    "patient_id": "patient_123",
    "ems_unit_id": "ems_unit_1",
    "hospital_id": "hospital_1",
    "created_at": "2026-01-18T10:35:00",
    "is_active": true
  }
]
```

#### 메시지 히스토리
```
GET /api/chat/rooms/{room_id}/messages?limit=50
```

**응답:**
```json
[
  {
    "id": "msg_1",
    "room_id": "room_123",
    "sender_id": "ems_unit_1",
    "sender_type": "ems",
    "message": "환자가 도착했습니다",
    "timestamp": "2026-01-18T10:35:00",
    "is_read": false
  }
]
```

#### 실시간 채팅 WebSocket
```
WebSocket /api/chat/ws/{room_id}
```

**메시지 전송 형식:**
```json
{
  "type": "message",
  "sender_id": "ems_unit_1",
  "sender_type": "ems",
  "message": "환자 상태 안정적입니다"
}
```

**수신 메시지 형식:**
```json
{
  "type": "message",
  "id": "msg_1",
  "sender_id": "ems_unit_1",
  "sender_type": "ems",
  "message": "환자 상태 안정적입니다",
  "timestamp": "2026-01-18T10:35:00"
}
```

## 헬스체크

```
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "app": "PulseRoute API",
  "version": "1.0.0"
}
```

## 환경 변수

```
# JWT 설정
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Firebase 설정
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# ML 서버 설정
ML_SERVER_URL=http://ml-server:8000
ML_SERVER_TIMEOUT=30

# 검색 설정
MAX_HOSPITAL_SEARCH_RADIUS_KM=50
```

## Firebase Firestore 컬렉션 구조

### users
```
{
  "id": "auto_generated",
  "email": "ems01@example.com",
  "password_hash": "bcrypt_hash",
  "type": "ems" | "hospital",
  "name": "Seoul EMS Unit 1",
  "created_at": timestamp
}
```

### patients
```
{
  "id": "auto_generated",
  "ems_unit_id": "user_id",
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "disease_code": "I21.0",
  "severity_code": "KTAS_1",
  "location": {
    "latitude": 37.5665,
    "longitude": 126.9780
  },
  "vital_signs": {
    "blood_pressure": "120/80",
    "pulse": 75,
    "temperature": 36.5
  },
  "status": "searching" | "matched" | "transferred",
  "created_at": timestamp
}
```

### transfer_requests
```
{
  "id": "auto_generated",
  "patient_id": "patient_id",
  "ems_unit_id": "user_id",
  "hospital_id": "user_id",
  "status": "pending" | "accepted" | "rejected" | "cancelled",
  "ml_score": 0.95,
  "distance_km": 5.2,
  "estimated_time_minutes": 15,
  "rejection_reason": "병상 부족",
  "created_at": timestamp,
  "updated_at": timestamp
}
```

### chat_rooms
```
{
  "id": "auto_generated",
  "patient_id": "patient_id",
  "ems_unit_id": "user_id",
  "hospital_id": "user_id",
  "created_at": timestamp,
  "is_active": true
}
```

### chat_messages
```
{
  "id": "auto_generated",
  "room_id": "room_id",
  "sender_id": "user_id",
  "sender_type": "ems" | "hospital",
  "message": "환자 상태 안정적입니다",
  "timestamp": timestamp,
  "is_read": false
}
```

## 에러 응답

모든 에러는 다음과 같은 형식으로 반환됩니다:

```json
{
  "detail": "에러 메시지"
}
```

### HTTP 상태 코드

- **200 OK**: 성공
- **400 Bad Request**: 잘못된 요청
- **401 Unauthorized**: 인증 실패
- **403 Forbidden**: 권한 없음
- **404 Not Found**: 리소스 없음
- **500 Internal Server Error**: 서버 오류

## 인증 헤더

모든 인증이 필요한 엔드포인트에 다음 헤더를 포함해야 합니다:

```
Authorization: Bearer {access_token}
```

## 로깅

모든 주요 작업은 로깅됩니다:

- 사용자 로그인
- 환자 등록
- 이송 요청 수락/거부
- 채팅 메시지 송수신

로그는 콘솔에 출력되며, 프로덕션 환경에서는 파일로 저장하도록 설정할 수 있습니다.

## ML 서버 연동

환자 등록 시 다음 흐름으로 진행됩니다:

1. 환자 정보와 반경 내 병원 목록을 ML 서버로 전송
2. ML 서버에서 매칭된 병원 리스트 반환 (점수순)
3. ML 서버 타임아웃 시 거리 기반 매칭 사용 (fallback)
4. 매칭된 병원들에 자동으로 이송 요청 생성

## 보안 고려사항

1. **JWT 시크릿 키**: 강력한 시크릿 키 사용 (최소 32자)
2. **HTTPS**: 프로덕션 환경에서 HTTPS 사용 필수
3. **CORS**: 프론트엔드 도메인만 허용하도록 설정
4. **Firebase Credentials**: git에서 제외 (.gitignore 확인)
5. **환경 변수**: .env 파일을 git에서 제외

## 문제 해결

### Firebase 연결 실패

```
Firebase 초기화 실패
```

해결책:
- firebase-credentials.json 파일 존재 확인
- Firebase 프로젝트 권한 확인
- 콘솔 로그에서 상세 에러 메시지 확인

### 토큰 검증 실패

```
유효하지 않은 토큰입니다
```

해결책:
- 토큰이 만료되지 않았는지 확인
- Authorization 헤더 형식 확인 (Bearer {token})
- JWT_SECRET_KEY가 올바른지 확인

### ML 서버 연결 실패

ML 서버 연결 실패 시 자동으로 거리 기반 매칭으로 폴백됩니다.

로그 확인:
```
ML 서버 연동 실패: ...
거리 기반 매칭 사용: N개 병원
```

## 배포

### Docker 배포

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 실행

```bash
docker build -t pulseroute-api .
docker run -p 8000:8000 --env-file .env pulseroute-api
```

## 라이선스

MIT License - PulseRoute 2026

## 기여

버그 보고 및 기능 요청은 이슈 페이지에서 관리합니다.

## 지원

문제 발생 시 로그를 확인하고 에러 메시지를 분석해주세요.

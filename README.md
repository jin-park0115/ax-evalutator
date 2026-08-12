# AX Evaluator

수강생 팀 편성, 평가 입력, 점수/석차 계산, 결과 공개를 위한 프로젝트입니다.

- `frontend/`: Django, Django Admin, Bootstrap 기반 화면/입력/사용자 흐름
- `backend/`: Python, Django ORM, PostgreSQL 기반 알고리즘/계산/데이터 정합성
- `docs/`: ERD/API 설계 문서

## 클론 후 실행 준비

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

기본 API 확인:

```bash
curl http://localhost:8000/api/health/
```

### 2. Frontend

새 터미널에서 실행합니다.

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8001
```

접속:

- Frontend: http://localhost:8001
- Django Admin: http://localhost:8001/admin/
- Backend API: http://localhost:8000/api/health/

## PostgreSQL

Docker가 있으면 아래 명령으로 PostgreSQL을 실행할 수 있습니다.

```bash
docker compose up -d postgres
```

로컬 PostgreSQL을 직접 쓰는 경우 아래 DB를 준비합니다.

- Backend: `ax_evaluator`
- Frontend: `ax_evaluator_frontend`

초기 개발 단계에서는 두 DB를 분리해 두었고, 실제 구현 단계에서 데이터 소유권과 API 계약을 기준으로 통합 여부를 결정합니다.

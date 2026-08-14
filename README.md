# AX Evaluator

수강생 팀 편성, 평가 입력, 점수/석차 계산, 결과 공개를 위한 프로젝트입니다.

- `project/`: Django 단일 프로젝트 (Django Template + Bootstrap + Django Admin + Django ORM + PostgreSQL)
- `docs/`: ERD/API 설계 문서

프론트엔드와 백엔드를 분리된 서버로 운영하지 않고, Django가 화면 렌더링(Template)부터
비즈니스 로직(ORM/services), 관리자 화면(Admin)까지 모두 담당합니다.

## 클론 후 실행 준비

```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

접속:

- 서비스 화면: http://localhost:8000
- Django Admin: http://localhost:8000/admin/

## PostgreSQL

로컬 PostgreSQL을 직접 쓰는 경우 아래 DB를 준비합니다.

- `ax_evaluator_frontend` (`.env`의 `POSTGRES_DB`와 동일하게 맞춥니다)

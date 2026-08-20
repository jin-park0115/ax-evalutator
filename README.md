# AX Evaluator

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

수강생 팀 편성, 평가 입력, 점수/석차 계산, 결과 공개를 위한 프로젝트입니다.

- `project/`: Django 단일 프로젝트 (Django Template + Bootstrap + Django Admin + Django ORM + PostgreSQL)
- `docs/`: ERD/API 설계 문서

프론트엔드와 백엔드를 분리된 서버로 운영하지 않고, Django가 화면 렌더링(Template)부터
비즈니스 로직(ORM/services), 관리자 화면(Admin)까지 모두 담당합니다.

## 팀 구성

| 역할 | 이름 |
|---|---|
| ![Backend](https://img.shields.io/badge/Backend-2E8B57?style=flat-square) | 전예진 |
| ![Backend](https://img.shields.io/badge/Backend-2E8B57?style=flat-square) | 채희주 |
| ![Frontend](https://img.shields.io/badge/Frontend-4169E1?style=flat-square) | 안형준 |
| ![Frontend](https://img.shields.io/badge/Frontend-4169E1?style=flat-square) | 장충만 |
| ![PM](https://img.shields.io/badge/PM-FF8C00?style=flat-square) | 김예주 |
| ![PM](https://img.shields.io/badge/PM-FF8C00?style=flat-square) | 박 진 |

## 요구 사항

- Python 3.10 이상

## 클론 후 실행 준비

**macOS / Linux**

```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

**Windows (PowerShell)**

```powershell
cd project
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

**Windows (cmd)**

```cmd
cd project
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

접속:

- 서비스 화면: http://localhost:8000
- Django Admin: http://localhost:8000/admin/

## 기술 스택

**Backend**

![Django](https://img.shields.io/badge/Django_5.2-092E20?style=flat-square&logo=django&logoColor=white)
![Django ORM](https://img.shields.io/badge/Django_ORM-092E20?style=flat-square&logo=django&logoColor=white)

**Database**

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![psycopg](https://img.shields.io/badge/psycopg-4169E1?style=flat-square&logo=postgresql&logoColor=white)

**Auth**

![django-allauth](https://img.shields.io/badge/django--allauth-092E20?style=flat-square&logo=django&logoColor=white)
![Google OAuth](https://img.shields.io/badge/Google_OAuth-4285F4?style=flat-square&logo=google&logoColor=white)

**Frontend**

![Django Template](https://img.shields.io/badge/Django_Template-092E20?style=flat-square&logo=django&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap_5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)

**Test / 환경 설정**

![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![python-decouple](https://img.shields.io/badge/python--decouple-.env-ECD53F?style=flat-square&logo=python&logoColor=black)

## 이미 클론한 저장소를 최신화할 때

`pull` 받은 뒤 의존성이 추가/변경됐을 수 있으니 아래 순서로 다시 맞춰줍니다.

```bash
git pull
pip install -r requirements.txt
python manage.py migrate
```

`requirements.txt`를 다시 설치하지 않으면 새로 추가된 패키지가 없어서 `ModuleNotFoundError`가 날 수 있습니다.

## 테스트 실행

```bash
pytest
```

## PostgreSQL

로컬 PostgreSQL을 직접 쓰는 경우 아래 DB를 준비합니다.

- `ax_evaluator_frontend` (`.env`의 `POSTGRES_DB`와 동일하게 맞춥니다)

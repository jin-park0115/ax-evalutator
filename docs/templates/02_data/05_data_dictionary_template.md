# 데이터 사전

## 기본 정보

| 항목 | 내용 |
|---|---|
| 기준 | `project/apps/*/models.py` |
| 목적 | 코드값(선택지), 공통 컬럼 규칙, 도메인 용어를 한 곳에서 관리하여 화면·API·문서 간 표기를 통일한다 |

## 1. 코드값 (Choices)

### USER.role — 계정 상태/역할

| 코드 | 표시명 | 설명 |
|---|---|---|
| `PENDING` | 승인대기 | 회원가입 직후 기본값. 관리자 승인 전 |
| `APPROVED` | 승인완료(역할미부여) | 승인은 됐으나 학생/관리자 역할이 아직 지정되지 않음 |
| `ADMIN` | 관리자 | 관리자 계정. `createsuperuser`는 반드시 이 값 |
| `STUDENT` | 학생 | 학생 계정 |

> "튜터"는 별도 `role` 값이 아니라 `is_staff = True`인 계정으로 구분한다.

### TEAM.eval_status — 팀 평가 진행 상태

| 코드 | 표시명 | 설명 |
|---|---|---|
| `NOT_OPENED` | 평가 미열람 | 기본값. 아직 평가 시작 전 |
| `OPEN` | 평가 진행 중 | 평가 가능 상태. 이후 다른 팀이 OPEN돼도 계속 수정 가능 |
| `CLOSED` | 평가 종료 | 평가 불가 |

상태 전이: `NOT_OPENED → OPEN → CLOSED` (역방향 전이 없음)

### EVALUATION_ROUND.status — 회차 전체 상태

| 코드 | 표시명 | 설명 |
|---|---|---|
| `draft` | 작성 중 | 기본값. 회차 설정 작성 중 |
| `ready` | 대기 | 설정 완료, 시작 대기 |
| `in_progress` | 진행 중 | 평가 진행 중 |
| `finished` | 종료 | 회차 종료 |

### EVALUATION_TEMPLATE.type — 평가 템플릿 유형

| 코드 | 표시명 | 설명 |
|---|---|---|
| `TEAM` | 팀 평가 | 팀 평가용 문항 세트 |
| `INDIVIDUAL` | 개인 평가 | 개인 평가용 문항 세트 |
| `TUTOR_INDIVIDUAL` | 튜터 개인 평가 | 튜터 개인 평가용 문항 세트 |
| `TUTOR_TEAM,` | 튜터 팀 평가 | 튜터 팀평가용 문항 세트 |

## 2. 공통 컬럼 규칙

| 컬럼명 | 타입 | 규칙 |
|---|---|---|
| `id` | BigAutoField | 모든 테이블의 PK. `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` |
| `created_at` | DATETIME | `auto_now_add=True`. 레코드 생성 시 1회만 자동 기록 |
| `updated_at` | DATETIME | `auto_now=True`. `EVALUATION_ROUND`에만 존재, save 시마다 갱신 |
| `*_id` (FK) | BigInteger | 대상 테이블의 `id` 참조. 기본 삭제 정책은 `on_delete=CASCADE` (부모 삭제 시 자식도 삭제) |
| `is_final` | BOOLEAN | `TEAM_EVALUATION`, `INDIVIDUAL_EVALUATION`에서 사용. `True`가 되면 이후 수정 불가 |
| `responses` | JSONField | 문항별 `{점수(1~5), 서술 의견}` 목록을 저장. 스키마는 `EVALUATION_TEMPLATE.criteria`를 따름 |

## 3. 점수/비율 필드 규칙

모든 점수는 **1~5점 스케일을 끝까지 유지**한다 — 100점으로 환산하는 단계는 없다.

| 필드 | 값 범위 | 규칙 |
|---|---|---|
| `EVALUATION_ROUND.team_weight` | 0~1 | 고정값 `0.4` |
| `EVALUATION_ROUND.individual_weight` | 0~1 | 고정값 `0.6` |
| `EVALUATION_ROUND.student_weight` + `tutor_weight` | 각 0~1 | 합이 반드시 `1.00` |
| 문항 점수 (`responses` 내부) | 1~5 (정수) | 각 문항마다 점수 + 서술 의견 |
| `TEAM_EVALUATION.score` / `INDIVIDUAL_EVALUATION.score` / `TUTOR_EVALUATION.score` | 1~5 (실수) | 해당 평가 1건의 문항 점수 평균 |
| `SCORE_RESULT.team_score` | 1~5 (실수) | 학생 팀 평가점수 + 튜터 팀 평가점수를 `student_weight`/`tutor_weight`로 가중합(튜터 평가 없으면 학생 값 그대로) |
| `SCORE_RESULT.individual_score` | 1~5 (실수) | 학생 개인 평가점수(5건 이상이면 최댓값·최솟값 절사평균) + 튜터 개인 평가점수를 가중합 |
| `SCORE_RESULT.final_score` | 1~5 (실수) | `team_score × 0.4 + individual_score × 0.6` |
| `SCORE_RESULT.rank` | 정수 | `final_score` 내림차순. 동점자는 같은 석차, 다음 석차는 동점자 수만큼 건너뜀(표준 경쟁 순위) |

계산식 상세와 예시는 [../01_requirements/business_rule_BR06.md](../01_requirements/business_rule_BR06.md)(팀 점수),
[BR07](../01_requirements/business_rule_BR07.md)(개인 점수), [BR08](../01_requirements/business_rule_BR08.md)(최종점수) 참고.
소수점은 계산 과정에서 별도로 반올림하지 않고 실수 값을 그대로 저장한다.

## 4. 도메인 용어

| 용어 | 정의 |
|---|---|
| 평가 회차 (Round) | 한 번의 팀 프로젝트 평가 사이클. 문항/가중치/공개 설정 단위 |
| 팀 평가 | 학생이 다른 팀 전체를 대상으로 하는 평가 |
| 개인 평가 | 학생이 다른 학생 개인을 대상으로 하는 평가 |
| 튜터 평가 | `is_staff=True` 계정이 팀 또는 개인을 대상으로 하는 평가 |
| 최종 제출 (`is_final`) | 평가자가 더 이상 수정하지 않기로 확정한 상태 |
| 시드 (`cumulative_seed`) | 팀 자동 편성에 활용하는 사용자별 누적 점수 기반 값 |
| 석차 (`rank`) | 회차별 최종 점수 기준 순위. 동점자는 최종 점수 → 가나다순으로 처리 |

## 5. 명명 규칙

- 테이블/모델명: 영문 단수, PascalCase (Django 모델) / 문서상 UPPER_SNAKE_CASE 병행 표기
- 컬럼명: snake_case
- 코드값(Choices): UPPER_SNAKE_CASE (예: `NOT_OPENED`) 또는 소문자 (예: `draft`) — 모델별로 상이하므로 [1. 코드값](#1-코드값-choices) 표를 기준으로 한다
- UNIQUE 제약 이름: `uq_<대상>_once` 형태

# 테이블 정의서

## 기본 정보

| 항목 | 내용 |
|---|---|
| 기준 | `project/apps/*/models.py` |
| PK 규칙 | 별도 명시가 없는 한 `id` (BigAutoField, auto-increment) |
| 공통 감사 컬럼 | `created_at` (대부분 테이블), `updated_at`(EVALUATION_ROUND만) |

> 코드값(선택지)의 상세 의미는 [05_data_dictionary_template.md](./05_data_dictionary_template.md)를 참고한다.

---

## USER

계정 정보. 학생/관리자 겸용이며 회원가입 승인 상태를 함께 관리한다. (`apps.accounts.User`, `AbstractUser` 상속)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 사용자 고유 ID |
| `username` | VARCHAR(150) | N | - | 로그인용 아이디. 한글/영문/숫자/`.@+-` 허용, UNIQUE |
| `email` | EMAIL | N | - | 이메일. UNIQUE. `USERNAME_FIELD`로 사용(로그인 ID) |
| `role` | VARCHAR(10) | N | `PENDING` | 계정 상태/역할 코드 |
| `is_staff` | BOOLEAN | N | False | 관리자 사이트 접근 및 튜터 권한 판별에 사용 |
| `is_superuser` | BOOLEAN | N | False | Django 슈퍼유저 여부 |
| `is_active` | BOOLEAN | N | True | 계정 활성화 여부 |
| `password` | VARCHAR | N | - | 해시된 비밀번호 |

제약조건: `username` UNIQUE, `email` UNIQUE

---

## TEAM

평가 회차별 팀 정보. (`apps.teams.Team`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 팀 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `name` | VARCHAR(100) | N | - | 팀 이름 |
| `presentation_order` | INTEGER | Y | NULL | 발표 순서 |
| `eval_status` | VARCHAR(20) | N | `NOT_OPENED` | 평가 진행 상태 코드 |
| `eval_opened_at` | DATETIME | Y | NULL | 평가 시작 일시 |
| `eval_closed_at` | DATETIME | Y | NULL | 평가 종료 일시 |
| `created_at` | DATETIME | N | auto_now_add | 생성 일시 |

---

## TEAM_MEMBER

팀-사용자 소속 관계. (`apps.teams.TeamMember`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 고유 ID |
| `team_id` | FK → TEAM | N | - | 소속 팀. `on_delete=CASCADE` |
| `student_id` | FK → USER | N | - | 소속 사용자(학생). `on_delete=CASCADE` |

제약조건: `UNIQUE(team_id, student_id)` (`uq_team_student_once`) — 동일 팀에 동일 사용자 중복 등록 방지

---

## TEAM_USER_SCORE_SEED

사용자별 회차별 누적 시드 점수. (`apps.teams.TeamUserScoreSeed`, `db_table = "TEAM_USER_SCORE_SEED"`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 시드 고유 ID |
| `user_id` | FK → USER | N | - | 사용자. `on_delete=CASCADE` |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `team_id` | FK → TEAM | N | - | 소속 팀. `on_delete=CASCADE` |
| `cumulative_seed` | FLOAT | N | 0.0 | 누적 시드 점수 |

제약조건: `UNIQUE(user_id, round_id)` (`uq_user_round_seed_once`)

---

## EVALUATION_ROUND

평가 회차 기본 정보 및 가중치·결과 공개 설정. (`apps.evaluations.EvaluationRound`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 회차 고유 ID |
| `name` | VARCHAR(100) | N | - | 평가 회차 이름 |
| `status` | VARCHAR(30) | N | `draft` | 회차 전체 상태 코드 |
| `start_at` | DATETIME | Y | NULL | 회차 시작 일시 |
| `end_at` | DATETIME | Y | NULL | 회차 종료 일시 |
| `team_weight` | FLOAT | N | 0.4 | 팀 성적 비율 (고정) |
| `individual_weight` | FLOAT | N | 0.6 | 개인 성적 비율 (고정) |
| `student_weight` | FLOAT | N | 0.5 | 학생 평가 비율 (회차별 설정) |
| `tutor_weight` | FLOAT | N | 0.5 | 튜터 평가 비율 (회차별 설정) |
| `team_first_rank_visible` | BOOLEAN | N | False | 팀 1위 공개 여부 |
| `team_rank_visible` | BOOLEAN | N | False | 전체 팀 순위 공개 여부 |
| `individual_score_visible` | BOOLEAN | N | False | 개인 점수 공개 여부 |
| `individual_rank_visible` | BOOLEAN | N | False | 개인 전체 석차 공개 여부 |
| `created_at` | DATETIME | N | auto_now_add | 생성 일시 |
| `updated_at` | DATETIME | N | auto_now | 수정 일시 |

비즈니스 규칙: `student_weight + tutor_weight = 1.00` ([BR-08](../01_requirements/business_rule_BR08.md) 등 관련 규칙 참고)

---

## EVALUATION_TEMPLATE

평가 회차별 문항 세트. (`apps.evaluations.EvaluationTemplate`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 문항 세트 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `type` | VARCHAR(20) | N | - | 템플릿 유형 코드 |
| `criteria` | JSONField | N | `{}` | 기본 문항 + 튜터 추가 문항 목록 |

---

## EVALUATION

사용자 간 단건 평가. (`apps.evaluations.Evaluation`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 평가 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `evaluator_id` | FK → USER | N | - | 평가자. `on_delete=CASCADE` |
| `target_id` | FK → USER | N | - | 평가 대상. `on_delete=CASCADE` |
| `score` | INTEGER | N | - | 평가 점수 |

제약조건: `UNIQUE(round_id, evaluator_id, target_id)` (`uq_evaluation_once`)

> `TEAM_EVALUATION`/`INDIVIDUAL_EVALUATION`/`TUTOR_EVALUATION`이 도입되기 전 단순 평가 모델로,
> 현재 세 하위 모델과 별도로 존재한다. 신규 기능은 하위 모델 기준으로 설계한다.

---

## TEAM_EVALUATION

학생의 팀 평가. (`apps.evaluations.TeamEvaluation`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 평가 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `evaluator_team_id` | FK → TEAM | N | - | 평가자 소속 팀. `on_delete=CASCADE` |
| `target_team_id` | FK → TEAM | N | - | 평가 대상 팀. `on_delete=CASCADE` |
| `submitted_by_id` | FK → USER | N | - | 평가 제출 사용자. `on_delete=CASCADE` |
| `score` | FLOAT | N | - | 계산된 팀 평가 점수 |
| `responses` | JSONField | N | `{}` | 문항별 점수 및 서술 의견 |
| `is_final` | BOOLEAN | N | False | 최종 제출 여부 |
| `created_at` | DATETIME | N | auto_now_add | 생성 일시 |

제약조건: `UNIQUE(round_id, evaluator_team_id, target_team_id, submitted_by_id)` (`uq_team_evaluation_once`)
관련 규칙: [BR-01](../01_requirements/business_rule_BR01.md) 자기 팀 팀 평가 제한

---

## INDIVIDUAL_EVALUATION

학생의 개인 평가. (`apps.evaluations.IndividualEvaluation`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 평가 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `team_id` | FK → TEAM | N | - | 평가 대상 학생의 소속 팀. `on_delete=CASCADE` |
| `evaluator_id` | FK → USER | N | - | 평가자. `on_delete=CASCADE` |
| `target_id` | FK → USER | N | - | 평가 대상. `on_delete=CASCADE` |
| `score` | FLOAT | N | - | 계산된 개인 평가 점수 |
| `responses` | JSONField | N | `{}` | 문항별 점수 및 서술 의견 |
| `is_final` | BOOLEAN | N | False | 최종 제출 여부 |
| `created_at` | DATETIME | N | auto_now_add | 생성 일시 |

제약조건: `UNIQUE(round_id, evaluator_id, target_id)` (`uq_individual_evaluation_once`)
관련 규칙: [BR-02~04](../01_requirements) 개인 평가 대상 제한

---

## TUTOR_EVALUATION

튜터(스태프 계정)의 팀·개인 평가. (`apps.evaluations.TutorEvaluation`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 평가 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `evaluator_id` | FK → USER | N | - | 평가한 튜터. `on_delete=CASCADE` |
| `user_id` | FK → USER | Y | NULL | 개인 평가 대상 사용자 |
| `team_id` | FK → TEAM | Y | NULL | 팀 평가 대상 |
| `score` | FLOAT | N | - | 계산된 평가 점수 |
| `responses` | JSONField | N | `{}` | 문항별 점수 및 서술 의견 |
| `created_at` | DATETIME | N | auto_now_add | 생성 일시 |

비고: `user_id`, `team_id` 중 실제 평가 대상에 해당하는 값만 채운다(둘 다 채우거나 둘 다 비울 수 있음 — 애플리케이션 레벨 검증 필요).
"튜터"는 별도 `role` 값이 아니라 `USER.is_staff = True` 로 구분한다.

---

## SCORE_RESULT

회차별 최종 점수 및 석차. (`apps.evaluations.ScoreResult`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 결과 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `user_id` | FK → USER | N | - | 사용자. `on_delete=CASCADE` |
| `team_id` | FK → TEAM | N | - | 소속 팀. `on_delete=CASCADE` |
| `team_score` | FLOAT | N | - | 최종 팀 평가점수 |
| `individual_score` | FLOAT | N | - | 최종 개인 평가점수 |
| `final_score` | FLOAT | N | - | 팀 40% + 개인 60% 합산 점수 |
| `rank` | INTEGER | Y | NULL | 석차 |

---

## ASSIGNMENT

회차별 과제 정보. (`apps.evaluations.Assignment`)

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|---|---|---|---|---|
| `id` | BigAutoField (PK) | N | auto | 과제 고유 ID |
| `round_id` | FK → EVALUATION_ROUND | N | - | 소속 평가 회차. `on_delete=CASCADE` |
| `title` | VARCHAR(200) | N | - | 과제 제목 |
| `description` | TEXT | Y | "" | 과제 설명 |
| `eval_start_at` | DATETIME | Y | NULL | 평가 시작 일시 |
| `eval_end_at` | DATETIME | Y | NULL | 평가 종료 일시 |

---

## 미구현 영역

`apps.students`, `apps.scoring`, `apps.results`는 이 문서 작성 시점 기준으로 모델이 비어 있다.
학생 프로필은 별도 테이블 없이 `USER`(role=`STUDENT`)로 관리되고, 점수 계산/결과 조회는
`apps.evaluations`의 테이블을 조회하는 서비스/뷰 로직으로 처리되는 것으로 보인다.
해당 앱에 모델이 추가되면 이 문서를 갱신한다.

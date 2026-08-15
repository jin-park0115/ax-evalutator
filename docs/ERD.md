# AX 평가 시스템 ERD

## 주요 엔티티

- `USER` : 사용자
- `TEAM` : 평가 회차별 팀
- `EVALUATION_ROUND` : 평가 회차 및 가중치/공개 설정
- `EVALUATION_TEMPLATE` : 평가 문항
- `TEAM_EVALUATION` : 학생의 팀 평가
- `INDIVIDUAL_EVALUATION` : 학생의 개인 평가
- `TUTOR_EVALUATION` : 튜터의 팀/개인 평가
- `SCORE_RESULT` : 평가 결과 및 석차
- `ASSIGNMENT` : 과제 정보
- `TEAM_USER_SCORE_SEED` : 사용자별 팀 성적 기반 누적 시드

---

## 평가 구조

### 학생 팀 평가

- 다른 팀 평가
- 자기 팀 평가 불가
- 문항마다 `1~5점`
- 문항마다 서술형 의견 작성
- 평가가 `OPEN`된 순간부터 평가 가능
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True` 이후 수정 불가

### 학생 개인 평가

- 다른 학생 평가
- 문항마다 `1~5점`
- 문항마다 서술형 의견 작성
- 평가가 `OPEN`된 순간부터 평가 가능
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True` 이후 수정 불가

### 튜터 평가

- 팀 평가 가능
- 개인 평가 가능
- 팀 평가만 사용할 수 있음
- 개인 평가만 사용할 수 있음
- 팀 + 개인 평가를 동시에 사용할 수 있음
- 문항마다 `1~5점`
- 문항마다 서술형 의견 작성

---

## 평가 진행 방식

이미 `OPEN`된 팀의 평가는 이후 다른 팀이 `OPEN`되어도 계속 수정할 수 있다.

※ 1조, 2조, 3조는 설명을 위한 예시이며 실제 팀 수에는 제한이 없다.

1. 1조 OPEN
2. 1조 평가 시작
3. 2조 OPEN
4. 1조 평가는 계속 수정 가능
5. 2조 평가 시작
6. 3조 OPEN
7. 1조와 2조 평가도 계속 수정 가능
8. 모든 평가가 끝난 후 최종 제출
9. 최종 제출 후 수정 불가

---

## 점수 구조

### 팀 / 개인 비율

- 팀 성적 : `40%` 고정
- 개인 성적 : `60%` 고정

### 학생 / 튜터 평가 비율

튜터가 평가 회차별로 설정한다.

- `student_weight + tutor_weight = 1.00`

예시:

- 학생 평가 `70%`
- 튜터 평가 `30%`

### 평가 점수 계산

각 문항은 `1~5점`으로 평가하고 서술형 의견을 작성한다.

여러 문항의 점수를 이용하여 해당 평가의 `team_score` 또는 `individual_score`를 계산한다.

팀 평가점수
= 학생 팀 평가점수 × `student_weight`
+ 튜터 팀 평가점수 × `tutor_weight`

개인 평가점수
= 학생 개인 평가점수 × `student_weight`
+ 튜터 개인 평가점수 × `tutor_weight`

최종점수
= 팀 평가점수 × `40%`
+ 개인 평가점수 × `60%`

### 계산 예시

학생 팀 평가점수 = 80점  
튜터 팀 평가점수 = 90점  
학생 평가 비율 = 70%  
튜터 평가 비율 = 30%

팀 평가점수
= 80 × 70% + 90 × 30%
= 83점

학생 개인 평가점수 = 70점  
튜터 개인 평가점수 = 90점

개인 평가점수
= 70 × 70% + 90 × 30%
= 76점

최종점수
= 83 × 40% + 76 × 60%
= 78.8점

---

# 테이블 정의

## USER

사용자 정보를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 사용자 고유 ID |
| `name` | VARCHAR | 사용자 이름 |
| `email` | VARCHAR | 이메일 |
| `role` | VARCHAR | 사용자 역할 |
| `team_id` | FK | 소속 팀 ID |

---

## TEAM

평가 회차별 팀 정보를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 팀 고유 ID |
| `name` | VARCHAR | 팀 이름 |
| `round_id` | FK | 평가 회차 ID |
| `presentation_order` | INT | 발표 순서 |
| `eval_status` | VARCHAR | 평가 상태 |
| `eval_opened_at` | DATETIME | 평가 시작 일시 |
| `eval_closed_at` | DATETIME | 평가 종료 일시 |
| `created_at` | DATETIME | 생성 일시 |

### TEAM 평가 상태

- `NOT_OPENED` : 아직 평가 시작 전
- `OPEN` : 평가 가능
- `CLOSED` : 평가 종료

`OPEN`된 팀은 이후 다른 팀이 `OPEN`되어도 계속 수정할 수 있다.

---

## EVALUATION_ROUND

평가 회차의 기본 정보와 가중치 및 결과 공개 설정을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 평가 회차 고유 ID |
| `name` | VARCHAR | 평가 회차 이름 |
| `status` | VARCHAR | 회차 전체 상태 |
| `start_at` | DATETIME | 회차 시작 일시 |
| `end_at` | DATETIME | 회차 종료 일시 |
| `team_weight` | FLOAT | 팀 성적 비율. `0.40` 고정 |
| `individual_weight` | FLOAT | 개인 성적 비율. `0.60` 고정 |
| `student_weight` | FLOAT | 학생 평가 비율. 튜터 설정 |
| `tutor_weight` | FLOAT | 튜터 평가 비율. 튜터 설정 |
| `team_first_rank_visible` | BOOLEAN | 팀 1위 공개 여부 |
| `team_rank_visible` | BOOLEAN | 전체 팀 순위 공개 여부 |
| `individual_score_visible` | BOOLEAN | 개인 점수 공개 여부 |
| `individual_rank_visible` | BOOLEAN | 개인 전체 석차 공개 여부 |

### 가중치 규칙

- `team_weight = 0.40`
- `individual_weight = 0.60`
- `student_weight + tutor_weight = 1.00`

---

## EVALUATION_TEMPLATE

평가 문항을 저장한다.

기본 문항은 교수님이 제공한 문항을 사용하고, 추가 문항은 튜터가 직접 입력한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 문항 고유 ID |
| `round_id` | FK | 평가 회차 ID |
| `type` | VARCHAR | 평가 템플릿 유형 |
| `criteria` | JSON | 기본문항 + 튜터 추가문항 목록 |

### 문항 구조

각 문항은 다음처럼 구성한다.

- 문항 1 → 점수 `1~5점` + 서술 의견
- 문항 2 → 점수 `1~5점` + 서술 의견
- 문항 3 → 점수 `1~5점` + 서술 의견

추가 문항은 튜터가 필요한 만큼 입력할 수 있다.

---

## TEAM_EVALUATION

학생이 다른 팀을 평가한 내용을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 평가 고유 ID |
| `round_id` | FK | 평가 회차 ID |
| `evaluator_team_id` | FK | 평가자 소속 팀 ID |
| `target_team_id` | FK | 평가 대상 팀 ID |
| `submitted_by` | FK | 평가 제출 사용자 ID |
| `score` | FLOAT | 해당 팀 평가의 계산 점수 |
| `responses` | JSON | 문항별 점수 및 서술 의견 |
| `is_final` | BOOLEAN | 최종 제출 여부 |
| `created_at` | DATETIME | 생성 일시 |

### 규칙

- 자기 팀 평가 불가
- 문항별 점수는 `1~5점`
- 문항별 서술 의견 작성
- `OPEN`된 팀 평가 가능
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True`이면 수정 불가

---

## INDIVIDUAL_EVALUATION

학생이 다른 학생을 평가한 내용을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 평가 고유 ID |
| `round_id` | FK | 평가 회차 ID |
| `team_id` | FK | 평가 대상 학생의 소속 팀 ID |
| `evaluator_id` | FK | 평가자 사용자 ID |
| `target_id` | FK | 평가 대상 사용자 ID |
| `score` | FLOAT | 해당 개인 평가의 계산 점수 |
| `responses` | JSON | 문항별 점수 및 서술 의견 |
| `is_final` | BOOLEAN | 최종 제출 여부 |
| `created_at` | DATETIME | 생성 일시 |

### 규칙

- 다른 학생 평가
- 문항별 점수는 `1~5점`
- 문항별 서술 의견 작성
- `OPEN`된 평가 가능
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True`이면 수정 불가

---

## TUTOR_EVALUATION

튜터가 팀 또는 개인을 평가한 내용을 저장한다.

팀 평가와 개인 평가를 하나만 사용할 수도 있고, 둘 다 사용할 수도 있다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 평가 고유 ID |
| `evaluator_id` | FK | 평가한 튜터 ID |
| `round_id` | FK | 평가 회차 ID |
| `user_id` | FK, NULL 가능 | 개인 평가 대상 사용자 ID |
| `team_id` | FK, NULL 가능 | 팀 평가 대상 팀 ID |
| `score` | FLOAT | 해당 튜터 평가의 계산 점수 |
| `responses` | JSON | 문항별 점수 및 서술 의견 |
| `created_at` | DATETIME | 생성 일시 |

### 평가 방식

- 팀 평가만 가능
- 개인 평가만 가능
- 팀 + 개인 평가 모두 가능
- 문항별 `1~5점`
- 문항별 서술형 의견 작성

`user_id`와 `team_id` 중 평가 대상에 해당하는 값이 사용된다.

---

## SCORE_RESULT

최종 평가 결과를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 결과 고유 ID |
| `round_id` | FK | 평가 회차 ID |
| `user_id` | FK | 사용자 ID |
| `team_id` | FK | 소속 팀 ID |
| `team_score` | FLOAT | 최종 팀 평가점수 |
| `individual_score` | FLOAT | 최종 개인 평가점수 |
| `final_score` | FLOAT | 팀 40% + 개인 60%로 계산한 최종 점수 |
| `rank` | INT | 석차 |

---

## ASSIGNMENT

과제 정보를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 과제 고유 ID |
| `round_id` | FK | 평가 회차 ID |
| `title` | VARCHAR | 과제 제목 |
| `description` | TEXT | 과제 설명 |
| `eval_start_at` | DATETIME | 평가 시작 일시 |
| `eval_end_at` | DATETIME | 평가 종료 일시 |

---

## TEAM_USER_SCORE_SEED

사용자별 팀 성적 기반 누적 시드를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT | 시드 고유 ID |
| `user_id` | FK | 사용자 ID |
| `round_id` | FK | 평가 회차 ID |
| `team_id` | FK | 소속 팀 ID |
| `cumulative_seed` | FLOAT | 누적 시드 점수 |

---

# 평가 문항 입력 방식

평가 문항은 별도 평가 문항 테이블을 추가하지 않고 `EVALUATION_TEMPLATE.criteria`에서 관리한다.

### 기본 문항

교수님이 제공한 프로젝트 기본 평가 문항을 사용한다.

### 추가 문항

튜터가 직접 문항을 입력할 수 있다.

### 각 문항

문항 1 → 5점 + 서술 의견  
문항 2 → 4점 + 서술 의견  
문항 3 → 3점 + 서술 의견

즉 평가자는 **각 문항마다 점수와 서술 의견을 작성**한다.

---

# 평가 최종 제출

### 평가 중

`is_final = False`

- 점수 수정 가능
- 서술 의견 수정 가능
- 여러 번 저장 가능

### 최종 제출

`is_final = True`

- 점수 수정 불가
- 서술 의견 수정 불가
- 다시 수정 불가

---

# 결과 공개 설정

튜터가 `EVALUATION_ROUND`에서 설정한다.

- 팀 1위 공개 여부
- 전체 팀 순위 공개 여부
- 개인 점수 공개 여부
- 개인 전체 석차 공개 여부

---

# 동점자 처리

1. 최종 점수
2. 가나다순
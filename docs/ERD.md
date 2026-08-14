# ERD

## 주요 엔티티

- `accounts` : 사용자 및 튜터 계정
- `rounds` : 평가 회차
- `teams` : 회차별 팀
- `team_members` : 학생-팀 소속 관계
- `team_evaluation` : 학생의 팀 평가
- `individual_evaluation` : 학생의 개인 평가
- `tutor_evaluation` : 튜터의 팀/개인 평가
- `score_result` : 평가 결과 및 석차
- `team_user_score_seed` : 사용자별 팀 성적 기반 누적 시드


## 평가 구조

### 학생 평가

#### TEAM_EVALUATION
학생이 다른 팀을 평가한다.

- 자기 팀은 평가할 수 없음
- 평가 점수 : 1~5점
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True`가 되면 수정 불가

#### INDIVIDUAL_EVALUATION
학생이 다른 학생을 평가한다.

- 평가 점수 : 1~5점
- 평가 이유를 작성할 수 있는 서술형 의견 포함
- 최종 제출 전까지 무제한 수정 가능
- `is_final = True`가 되면 수정 불가


### 튜터 평가

#### TUTOR_EVALUATION
튜터가 팀과 개인을 평가한다.

- 팀 평가 : `team_id`
- 개인 평가 : `user_id`
- 평가 점수 : 1~5점
- `round_id` : 평가 회차
- `created_at` : 생성 일시


## 평가 진행 방식

평가가 OPEN 되는 순간부터 평가할 수 있다.

이미 OPEN 된 평가는 이후 다른 팀의 평가가 OPEN 되어도 계속 수정할 수 있다.

예시:

1. 1조 OPEN
2. 1조 평가 시작
3. 2조 OPEN
4. 1조 평가는 계속 수정 가능
5. 2조 평가 시작
6. 3조 OPEN
7. 1조와 2조 평가도 계속 수정 가능
8. 모든 평가가 끝난 후 최종 제출
9. 최종 제출 후 모든 평가 수정 불가


## 점수 구조

### 팀 / 개인 비율

최종 점수에서 팀과 개인의 비율은 고정이다.

- 팀 성적 : 40%
- 개인 성적 : 60%


### 학생 평가 / 튜터 평가 비율

학생 평가와 튜터 평가의 비율은 튜터가 설정한다.

학생 평가 + 튜터 평가 = 100%

예시:

학생 평가 70% / 튜터 평가 30%

팀 성적:

- 학생 팀 평가 : 40% × 70% = 28%
- 튜터 팀 평가 : 40% × 30% = 12%

개인 성적:

- 학생 개인 평가 : 60% × 70% = 42%
- 튜터 개인 평가 : 60% × 30% = 18%

최종:

- 학생 팀 평가 : 28%
- 튜터 팀 평가 : 12%
- 학생 개인 평가 : 42%
- 튜터 개인 평가 : 18%


## 주요 테이블

### TEAM_EVALUATION

학생이 다른 팀을 평가하는 테이블.

- `id` : 고유 식별자
- `round_id` : 평가 회차 ID
- `evaluator_team_id` : 평가자 소속 팀 ID
- `target_team_id` : 평가 대상 팀 ID
- `submitted_by` : 평가 제출 사용자 ID
- `score` : 평가 점수 (1~5점)
- `is_final` : 최종 제출 여부
  - `False` : 수정 가능
  - `True` : 수정 불가
- `created_at` : 생성 일시


### INDIVIDUAL_EVALUATION

학생이 다른 학생을 평가하는 테이블.

- `id` : 고유 식별자
- `round_id` : 평가 회차 ID
- `team_id` : 평가 대상 학생의 팀 ID
- `evaluator_id` : 평가자 사용자 ID
- `target_id` : 평가 대상 사용자 ID
- `score` : 평가 점수 (1~5점)
- `comment` : 평가 이유 및 서술형 의견
- `is_final` : 최종 제출 여부
  - `False` : 수정 가능
  - `True` : 수정 불가
- `created_at` : 생성 일시


### TUTOR_EVALUATION

튜터가 팀과 개인을 평가하는 테이블.

- `id` : 고유 식별자
- `round_id` : 평가 회차 ID
- `user_id` : 개인 평가 대상 사용자 ID
- `team_id` : 팀 평가 대상 팀 ID
- `score` : 평가 점수 (1~5점)
- `created_at` : 생성 일시


### SCORE_RESULT

평가 결과를 저장하는 테이블.

- `id` : 고유 식별자
- `round_id` : 평가 회차 ID
- `user_id` : 사용자 ID
- `team_id` : 소속 팀 ID
- `team_score` : 팀 성적
- `individual_score` : 개인 성적
- `final_score` : 최종 점수
- `rank` : 석차


### TEAM_USER_SCORE_SEED

사용자별 팀 성적 기반 누적 시드를 저장하는 테이블.

- `id` : 고유 식별자
- `user_id` : 사용자 ID
- `round_id` : 평가 회차 ID
- `team_id` : 소속 팀 ID
- `cumulative_seed` : 누적 시드 점수


## 동점자 처리

동점인 경우 다음 기준으로 처리한다.

1. 최종 점수
2. 가나다순
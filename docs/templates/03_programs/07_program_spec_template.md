# 프로그램 명세서

## 기본 정보

| 항목 | 내용 |
|---|---|
| 기준 | [06_program_list_template.md](./06_program_list_template.md)의 프로그램 목록 |
| 표기 | 각 프로그램은 개요 / 입력 / 처리 로직 / 출력 / 관련 규칙·테이블 / 비고 순으로 기술 |

---

## P-01 홈

- **개요**: 서비스 진입 화면. 별도 조건 분기 없이 정적 렌더링.
- **입력**: 없음
- **처리 로직**: `home.html` 렌더링
- **출력**: 홈 화면
- **관련 테이블**: 없음

---

## P-02 회원가입

- **개요**: 이메일/아이디/비밀번호로 계정을 생성하고 승인 대기 상태로 저장한다.
- **입력**: `email`, `username`, `password`, `password_confirm` (`CustomUserCreationForm`)
- **처리 로직**: 폼 검증 성공 시 `User.role = PENDING`으로 저장 → 로그인 화면으로 리다이렉트, 성공 메시지 표시
- **출력**: 가입 완료 메시지, 로그인 페이지로 이동
- **관련 테이블**: USER
- **비고**: 이 시점에는 로그인이 불가하다(P-03 참고). 관리자 승인 + 역할 부여(P-05)가 끝나야 로그인 가능.

---

## P-03 로그인 (일반 + 소셜)

- **개요**: 이메일/비밀번호 로그인과 소셜 로그인(allauth)을 모두 지원하되, 계정 상태에 따라 로그인 가능 여부가 갈린다.
- **입력**: `email`, `password` (일반) / 소셜 프로바이더 인증 정보
- **처리 로직**:
  - 일반 로그인은 `RoleBasedAuthBackend`를 사용. 비밀번호가 맞아도 `role`이 `STUDENT`/`ADMIN`이 아니면(`PENDING`/`APPROVED`) 인증 실패 처리
  - 소셜 로그인은 `CustomSocialAccountAdapter.pre_social_login`에서 기존 사용자의 `role`이 `PENDING`/`APPROVED`이면 로그인 차단 후 에러 메시지와 함께 로그인 화면으로 리다이렉트. 신규 소셜 가입자는 `role = PENDING`으로 생성
- **출력**: 성공 시 홈으로 이동, 실패 시 에러 메시지
- **관련 테이블**: USER
- **관련 코드**: `apps/accounts/backends.py`, `apps/accounts/adapters.py`

---

## P-04 로그아웃

- **개요**: 세션 종료 후 로그인 화면으로 이동
- **입력**: 없음
- **처리 로직**: `django.contrib.auth.logout` 호출
- **출력**: 로그인 페이지로 리다이렉트

---

## P-05 회원 승인 관리

- **개요**: 관리자가 가입 신청자를 승인/역할부여/거절 처리하는 화면.
- **입력**: `user_id`, (역할 부여 시) `role`
- **처리 로직**: 2단계 상태 전이
  1. `approve_user`: `PENDING → APPROVED` (역할 미부여 상태)
  2. `assign_role`: `APPROVED → STUDENT | ADMIN`. `ADMIN` 선택 시 `is_staff = True`도 함께 설정. 이 시점부터 로그인 가능
  - `reject_user`: 사용자 레코드를 DB에서 완전히 삭제(`delete()`)
- **출력**: 승인/역할부여/거절 결과 메시지, 목록 갱신
- **관련 테이블**: USER
- **비고**: `reject_user`는 소프트 삭제가 아니라 하드 삭제다. 재가입 시 새 계정으로 처리된다.

---

## P-06 학생 홈

- **개요**: 로그인한 학생에게 진행 중인 평가 회차 상태와 소속 팀을 보여준다.
- **입력**: 없음(세션 사용자 기준)
- **처리 로직**: `EvaluationRound.status = IN_PROGRESS`인 회차 존재 여부로 `state`(`open`/`before`) 결정, `get_my_team(user)`로 소속 팀 조회
- **출력**: 회차 상태, 소속 팀 정보
- **관련 테이블**: EVALUATION_ROUND, TEAM_MEMBER

---

## P-07 내 팀 조회

- **개요**: 내가 속한 팀과 팀원 목록을 보여준다.
- **입력**: 없음(세션 사용자 기준)
- **처리 로직**: `TeamMember`에서 본인 소속 팀을 찾고, 같은 팀의 전체 `TeamMember`를 조회
- **출력**: 팀 정보, 팀원 목록
- **관련 테이블**: TEAM, TEAM_MEMBER

---

## P-08 결과 조회

- **개요**: 회차별 본인 점수/석차를 회차의 공개 설정에 따라 노출한다.
- **입력**: 없음(세션 사용자 기준)
- **처리 로직**: 진행 중 회차(없으면 최신 회차)의 `ScoreResult`를 조회. `team_rank_visible`/`individual_score_visible`/`individual_rank_visible` 각 플래그가 `False`면 해당 값은 `None`으로 마스킹
- **출력**: `team_score`(조건부), `personal_score`(조건부), `final_score`(항상), `rank`(조건부)
- **관련 테이블**: EVALUATION_ROUND, SCORE_RESULT
- **관련 규칙**: [BR-10](../01_requirements/business_rule_BR10.md) 순위 공개 설정
- **비고**: 함수 주석상 `calculate_round()`/`score_service.get_visible_result()`로 교체 예정인 임시 구현

---

## P-09 수강생 관리 API

- **개요**: 관리자가 학생 계정을 조회/수정/삭제(대기 상태로 되돌림)하는 JSON API.
- **입력**: `student_list` — 없음 / `update_student` — `username`, `email` / `delete_student` — 없음(`student_id` path)
- **처리 로직**: `update_student`는 이메일 중복 검사 후 저장. `delete_student`는 실제 삭제가 아니라 `role = PENDING`으로 되돌림(재승인 필요)
- **출력**: JSON 응답
- **관련 테이블**: USER
- **비고**: 대응하는 화면 템플릿을 찾지 못했다 — 프런트 연동 여부 확인 필요.

---

## P-10 회차 관리

- **개요**: 평가 회차를 생성하고 상태(`draft→ready→in_progress→finished`)와 팀 1위 공개 여부를 변경한다.
- **입력**: 생성 시 `title`, `start_date`, `end_date`, `student_weight`, `tutor_weight` / 상태 변경 시 `status` / 공개 토글 시 없음(`round_id`만)
- **처리 로직**: 생성은 `EvaluationRound.objects.create(...)`. 상태 변경은 `Status.values`에 포함된 값만 반영. 1위 공개는 불리언 토글
- **출력**: 회차 목록, 갱신된 상태
- **관련 테이블**: EVALUATION_ROUND

---

## P-11 팀 편성 (+ P-11a 팀 편성 API)

- **개요**: 회차별 팀 생성, 학생 배정/이동, 퍼센타일 기반 자동 편성, 편성 확정을 수행한다. 화면(`team_build`)이 `/teams/...` API들을 JS로 호출하는 구조.
- **입력**:
  - `create_team`: `round_id`, `name`
  - `assign_or_move_student`: `student_id`, `team_id`
  - `get_percentile_preview` / `auto_assign_teams`: `round_id`, `thresholds`, `team_count`(선택), `fixed_student_ids`(선택), `excluded_student_ids`(선택)
  - `confirm_team_assignment`: `round_id`
- **처리 로직**:
  - 모든 변경 API는 `is_round_editable(round)`(상태가 `draft`/`ready`일 때만)로 편집 가능 여부를 검사
  - `auto_assign_teams`: 이전 회차 시드 기록(`TeamUserScoreSeed`)이 있으면 `assign_seed_based_teams()`로 시드 기반 편성, 없으면 무작위 균등 배정(`calculate_optimal_team_count()`로 팀 수 자동 산출)
  - `confirm_team_assignment`: 팀이 1개 이상 존재해야 하며, 성공 시 회차 상태를 `READY`로 전환
  - `open_team_presentation`: `Team.eval_opened_at`이 비어 있을 때만 현재 시각으로 세팅하고 `eval_status = OPEN`. 누적 오픈 방식이라 이후 다른 팀이 열려도 되돌리지 않음
- **출력**: 팀/배정 결과 JSON, 갱신된 팀 편성 화면
- **관련 테이블**: TEAM, TEAM_MEMBER, TEAM_USER_SCORE_SEED, EVALUATION_ROUND
- **관련 규칙**: [BR-09](../01_requirements/business_rule_BR09.md) 자동 팀 편성

---

## P-12 팀 평가 현황 (목업)

- **개요**: 팀별 평가 점수/상태를 보여주는 화면. **하드코딩된 목업 데이터**를 렌더링하며 DB 조회가 없다.
- **입력**: 없음
- **처리 로직**: `views_tutor.py`에 정의된 고정 리스트(3개 팀)를 그대로 템플릿에 전달
- **출력**: 목업 팀 평가 목록
- **비고**: 실제 데이터 연동 필요(관련 테이블: TEAM_EVALUATION). P-16(평가 현황 대시보드)이 실 데이터 기반 현황을 이미 제공하고 있어 이 화면과의 정리/통합이 필요해 보인다.

---

## P-13 개인 평가 현황 (목업)

- **개요**: 팀원 개인 평가 점수/상태를 보여주는 화면. **하드코딩된 목업 데이터**를 렌더링하며 DB 조회가 없다.
- **입력**: 없음
- **처리 로직**: `views_tutor.py`에 정의된 고정 리스트(6명)를 그대로 템플릿에 전달
- **출력**: 목업 개인 평가 목록
- **비고**: 실제 데이터 연동 필요(관련 테이블: INDIVIDUAL_EVALUATION).

---

## P-14 평가 문항 템플릿 관리

- **개요**: 회차별 팀/개인/튜터 평가 문항 세트를 등록/조회한다.
- **입력**: `round_id`, `type`(TEAM/INDIVIDUAL/TUTOR), 문항 목록(`item_key[]`, `item_text[]`)
- **처리 로직**: `key`/`text`가 모두 있는 문항만 `criteria` 리스트로 구성해 `EvaluationTemplate.objects.update_or_create(round_id, type, defaults={"criteria": ...})` — 동일 회차·유형 조합은 덮어쓰기
- **출력**: 템플릿 목록, 등록 결과
- **관련 테이블**: EVALUATION_TEMPLATE

---

## P-15 결과 공개 설정

- **개요**: 회차별 팀 1위/전체 팀 순위/개인 점수/개인 석차 공개 여부를 설정한다.
- **입력**: `round_id`, 체크박스 4종(`team_first_rank_visible`, `team_rank_visible`, `individual_score_visible`, `individual_rank_visible`)
- **처리 로직**: 체크박스 존재 여부(`"필드명" in request.POST`)로 불리언 값을 그대로 저장
- **출력**: 갱신된 공개 설정
- **관련 테이블**: EVALUATION_ROUND
- **관련 규칙**: [BR-10](../01_requirements/business_rule_BR10.md)

---

## P-16 평가 현황 대시보드

- **개요**: 회차별 학생 개인 평가 제출률과 팀 평가 완료 현황, 미제출자 목록을 보여준다.
- **입력**: `round_id`(선택, 없으면 최신 회차)
- **처리 로직**:
  - 개인 평가: 해당 회차에서 `IndividualEvaluation.is_final=True`인 레코드가 하나라도 있는 학생을 "제출 완료"로 간주(개인 상호평가는 팀원 전체를 한 번에 제출하는 구조이기 때문)
  - 팀 평가: 팀별로 평가한 `evaluator_team` 수가 `전체 팀 수 - 1`(자기 팀 제외 전원) 이상이면 "완료"로 간주
- **출력**: 완료/잔여 인원·팀 수, 완료율(%), 미제출자 목록
- **관련 테이블**: TEAM, TEAM_MEMBER, TEAM_EVALUATION, INDIVIDUAL_EVALUATION

---

## P-17 팀 평가 목록/작성

- **개요**: 학생이 발표(평가)가 열린 다른 팀을 평가한다. 임시저장 방식.
- **입력**: (목록) 없음 / (작성) `item_{key}` 문항별 점수(1~5)
- **처리 로직**:
  - 목록: 현재 회차에서 `eval_opened_at`이 설정된 팀 중 내 팀 제외, 오픈 순서대로 정렬. 누적 오픈이라 한 번 열리면 계속 목록에 남는다
  - 작성: 자기 팀 평가 시도 차단, 미오픈 팀 차단, 최종 제출 완료 후 접근 차단. 모든 문항 응답 시 평균 점수를 계산해 `TeamEvaluation`을 `update_or_create`(=재저장 시 덮어쓰기), `is_final=False`로 저장
- **출력**: 평가 가능 팀 목록 / 저장 결과 메시지
- **관련 테이블**: TEAM, TEAM_EVALUATION, EVALUATION_TEMPLATE
- **관련 규칙**: [BR-01](../01_requirements/business_rule_BR01.md) 자기 팀 평가 제한

---

## P-18 개인(동료) 평가 작성

- **개요**: 학생이 같은 팀 동료 전원을 한 화면에서 평가한다. 임시저장 방식.
- **입력**: 팀원별·문항별 `item_{student_id}_{key}` 점수(1~5)
- **처리 로직**: 최종 제출 완료 시 접근 차단. 팀원 각각에 대해 모든 문항 응답이 있어야 저장 진행(하나라도 누락되면 해당 팀원 처리 시점에서 즉시 실패 메시지 반환). 평균 점수 계산 후 `IndividualEvaluation`을 `update_or_create`, `is_final=False`
- **출력**: 팀원별 평가 폼, 저장 결과 메시지
- **관련 테이블**: TEAM_MEMBER, INDIVIDUAL_EVALUATION, EVALUATION_TEMPLATE
- **관련 규칙**: 개인 평가 대상 제한 규칙(자기 자신 제외 — `.exclude(student=request.user)`)

---

## P-19 평가 최종 제출

- **개요**: 학생이 이번 회차에 임시저장해 둔 팀 평가·개인 평가 전체를 한 번에 잠근다.
- **입력**: 없음
- **처리 로직**: 이미 최종 제출했으면 에러 처리. 아니면 해당 사용자의 `TeamEvaluation`/`IndividualEvaluation` 레코드를 트랜잭션으로 일괄 `is_final=True` 갱신
- **출력**: 완료 메시지, 목록으로 리다이렉트
- **관련 테이블**: TEAM_EVALUATION, INDIVIDUAL_EVALUATION
- **비고**: 팀별 개별 제출/잠금은 없고, 회차 단위 일괄 잠금이다. 확정 규칙(2026-08-17 합의)에 따른 동작.

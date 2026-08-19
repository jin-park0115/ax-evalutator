# 인수 기준 (Acceptance Criteria)

## 기본 정보

| 항목 | 내용 |
|---|---|
| 형식 | Given-When-Then |
| 기준 | [06_program_list_template.md](./06_program_list_template.md) 프로그램별 실제 View 로직 |
| 연결 문서 | [01_requirements/02_traceability_matrix_template.md](../01_requirements/02_traceability_matrix_template.md) (REQ-ID), [01_requirements/business_rule_BR*.md](../01_requirements) (BR-ID) |

---

## P-02 회원가입

- **AC-02-1**
  - Given 비로그인 사용자가 회원가입 폼에 이메일/아이디/비밀번호를 올바르게 입력했을 때
  - When 가입을 제출하면
  - Then 계정이 `role=PENDING`으로 생성되고 로그인 화면으로 이동하며 "관리자 승인 후 로그인 가능" 안내가 뜬다
- **AC-02-2**
  - Given 이미 존재하는 이메일로 가입을 시도했을 때
  - When 폼을 제출하면
  - Then 가입이 거부되고 에러가 표시된다 (`email` UNIQUE)

## P-03 로그인

- **AC-03-1**
  - Given `role=STUDENT` 또는 `role=ADMIN`인 계정의 올바른 이메일/비밀번호로
  - When 로그인을 시도하면
  - Then 로그인에 성공하고 홈 화면으로 이동한다
- **AC-03-2**
  - Given `role=PENDING` 또는 `role=APPROVED`인 계정의 올바른 비밀번호로
  - When 로그인을 시도하면
  - Then 로그인이 거부되고 "승인 대기 중" 계열 에러가 표시된다
- **AC-03-3**
  - Given 기존 계정 이메일로 소셜 로그인을 시도했고 해당 계정이 `PENDING`/`APPROVED`일 때
  - When 소셜 인증이 완료되면
  - Then 로그인 화면으로 리다이렉트되며 승인 대기 에러 메시지가 표시된다

## P-05 회원 승인 관리

- **AC-05-1**
  - Given 관리자가 `PENDING` 계정 목록을 볼 때
  - When "승인"을 누르면
  - Then 해당 계정이 `APPROVED`로 전환되고, 아직 로그인은 불가하다
- **AC-05-2**
  - Given `APPROVED` 상태 계정에
  - When 관리자가 역할(`STUDENT`/`ADMIN`)을 지정하면
  - Then 역할이 저장되고(`ADMIN`인 경우 `is_staff=True`도 함께 설정) 해당 계정은 이후 로그인이 가능해진다
- **AC-05-3**
  - Given 가입 신청 계정에
  - When 관리자가 "거절"을 누르면
  - Then 해당 계정 레코드가 DB에서 완전히 삭제된다(복구 불가)

## P-08 결과 조회

- **AC-08-1**
  - Given 회차의 `individual_score_visible=False`인 상태에서 본인의 `ScoreResult`가 존재할 때
  - When 결과 조회 화면에 진입하면
  - Then `personal_score`는 `None`(비공개)으로 표시되고 `final_score`는 항상 표시된다
  - 관련: [BR-10](../01_requirements/business_rule_BR10.md)
- **AC-08-2**
  - Given 아직 진행 중이거나 종료된 회차가 하나도 없을 때
  - When 결과 조회 화면에 진입하면
  - Then 결과 없음으로 처리된다(`None`)

## P-10 회차 관리

- **AC-10-1**
  - Given 관리자가 `title`, `start_date`, `end_date`를 모두 입력했을 때
  - When 회차 생성을 제출하면
  - Then 새 `EvaluationRound`가 `status=draft`로 생성된다
- **AC-10-2**
  - Given 필수 입력값(`title`/`start_date`/`end_date`) 중 하나라도 비어 있을 때
  - When 제출하면
  - Then 회차가 생성되지 않고 목록 화면이 그대로 다시 보인다

## P-11 / P-11a 팀 편성

- **AC-11-1**
  - Given 회차 상태가 `draft` 또는 `ready`일 때
  - When 관리자가 학생을 특정 팀으로 배정하면
  - Then 해당 학생의 기존 팀 배정이 삭제되고 새 팀으로 배정된다(팀 중복 소속 없음)
- **AC-11-2**
  - Given 회차 상태가 `in_progress` 또는 `finished`일 때
  - When 관리자가 팀 생성/배정/자동편성/확정 API를 호출하면
  - Then 400 에러로 거부된다(`is_round_editable` 검사)
  - 관련: 팀 편성 확정 후 잠금
- **AC-11-3**
  - Given 이전 회차의 `TeamUserScoreSeed` 기록이 존재할 때
  - When 자동 편성을 실행하면
  - Then 누적 시드 점수 기반으로 팀이 편성된다(무작위 편성이 아님)
  - 관련: [BR-09](../01_requirements/business_rule_BR09.md)
- **AC-11-4**
  - Given 이전 회차 시드 기록이 전혀 없을 때(최초 회차)
  - When 자동 편성을 실행하면
  - Then 인원이 팀별로 균등하게 무작위 배정된다
- **AC-11-5**
  - Given 회차에 팀이 1개 이상 편성돼 있을 때
  - When 관리자가 편성을 확정하면
  - Then 회차 상태가 `READY`로 바뀌고 더 이상 편성을 수정할 수 없다
- **AC-11-6**
  - Given 관리자가 특정 팀의 발표를 처음 여는 시점에
  - When "평가 오픈"을 누르면
  - Then 해당 팀 `eval_status=OPEN`, `eval_opened_at`이 기록되고, 이후 다른 팀이 열려도 이 팀은 닫히지 않는다

## P-17 팀 평가 목록/작성

- **AC-17-1**
  - Given 로그인한 학생이 자기 팀을 평가 대상 목록에서 찾으려 할 때
  - When 팀 평가 목록 화면을 열면
  - Then 자기 소속 팀은 목록에 나타나지 않는다
  - 관련: [BR-01](../01_requirements/business_rule_BR01.md)
- **AC-17-2**
  - Given 아직 발표(평가)가 열리지 않은 팀(`eval_opened_at`이 비어 있음)에
  - When 학생이 평가 폼 URL로 직접 접근하면
  - Then 에러 메시지와 함께 목록으로 리다이렉트된다(서버 측에서 차단)
- **AC-17-3**
  - Given 학생이 이미 회차 최종 제출을 완료했을 때
  - When 팀 평가 폼에 접근하면
  - Then 수정이 차단되고 에러 메시지가 표시된다
- **AC-17-4**
  - Given 학생이 문항 일부만 응답하고 제출했을 때
  - When 폼을 저장하면
  - Then "모든 문항에 응답해야 합니다" 에러가 표시되고 저장되지 않는다
- **AC-17-5**
  - Given 같은 팀을 이미 임시저장으로 평가한 적이 있을 때
  - When 다시 저장하면
  - Then 기존 레코드가 덮어써진다(신규 행 생성이 아님, `update_or_create`)

## P-18 개인(동료) 평가 작성

- **AC-18-1**
  - Given 로그인한 학생이 동료 평가 화면을 열 때
  - When 팀원 목록을 확인하면
  - Then 본인은 목록에서 제외되어 있다
- **AC-18-2**
  - Given 팀원 중 한 명에 대해 문항 일부만 응답했을 때
  - When 저장을 시도하면
  - Then 해당 팀원 이름을 포함한 에러 메시지가 표시되고 전체 저장이 중단된다
- **AC-18-3**
  - Given 학생이 이미 회차 최종 제출을 완료했을 때
  - When 동료 평가 화면에서 저장을 시도하면
  - Then 저장이 차단된다

## P-19 평가 최종 제출

- **AC-19-1**
  - Given 학생이 팀 평가/개인 평가를 임시저장해 둔 상태에서
  - When 최종 제출을 누르면
  - Then 해당 학생의 모든 `TeamEvaluation`/`IndividualEvaluation`이 한 번에 `is_final=True`로 바뀌고, 이후 어떤 평가도 수정할 수 없다
- **AC-19-2**
  - Given 이미 최종 제출을 완료한 학생이
  - When 최종 제출을 다시 누르면
  - Then "이미 최종 제출을 완료했습니다" 에러가 표시되고 아무 변화가 없다
- **AC-19-3**
  - Given 학생이 오픈된 팀 중 일부만 평가했거나 팀원 중 일부만 개인 평가한 상태에서(완료하지 않은 상태)
  - When 최종 제출을 누르면
  - Then 제출이 거부되지 않고 성공한다 — 그 시점까지 저장된 평가만 잠기고, 평가하지 않은 대상은 그대로 미제출로 남는다
  - 관련: [BR-11](../01_requirements/business_rule_BR11.md) 평가 최종 제출 조건(부분 제출 허용)
- **AC-19-4**
  - Given 학생이 팀 평가/개인 평가를 한 건도 임시저장하지 않은 상태에서
  - When 최종 제출을 누르면
  - Then 오류 없이 제출이 완료된다(잠글 대상이 없을 뿐 빈 제출 자체는 허용)
  - 관련: [BR-11](../01_requirements/business_rule_BR11.md)

## 매핑 참고

프로그램별 AC와 요구사항 추적을 위해 [02_traceability_matrix_template.md](../01_requirements/02_traceability_matrix_template.md)의
`Test Case` 컬럼에 위 AC-ID(예: `AC-17-1`)를 함께 기재하는 것을 권장한다. 현재 매트릭스는 `TC-XXX-001` 단위로만 구분돼 있어
프로그램 단위 추적이 되지 않는다(참고용 지적, 해당 문서는 이 작업에서 수정하지 않음).

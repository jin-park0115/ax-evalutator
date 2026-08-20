# 프로그램 목록

## 기본 정보

| 항목 | 내용 |
|---|---|
| 기준 | `project/config/urls.py`(ROOT_URLCONF), 각 앱의 `urls.py`/`views*.py`, `templates/` |
| 프로그램 ID 규칙 | `P-XX` (2자리 순번) |
| 상태 값 | 정상(실 DB 연동) / 목업(하드코딩 데이터) / API-Only(전용 화면 없음) |

> 코드 조사 결과 `apps/evaluations`에 학생 평가 화면이 **두 벌** 구현돼 있다.
> ① `views_eval.py` — 루트 `urls.py`에 직접 연결(`/eval/...`), 템플릿 존재, 실제 서비스되는 경로.
> ② `view_eval.py` — `apps/evaluations/urls.py`에 연결(`/student/evaluation/...`), `student/evaluation.html` 등
> 템플릿이 `templates/` 아래 존재하지 않아 호출 시 `TemplateDoesNotExist`가 발생한다.
> 아래 목록은 ①만 정식 프로그램으로 포함하고, ②는 "미사용/중복 구현" 표로 별도 표기한다(코드는 수정하지 않음).

## 1. 인증 / 계정

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-01 | 홈 | 화면 | `/` | `accounts.views.home` | `home.html` | 전체(비로그인 포함) | 정상 |
| P-02 | 회원가입 | 화면 | `/accounts/signup/` | `accounts.views.signup` | `accounts/signup.html` | 비로그인 | 정상 |
| P-03 | 로그인 (일반 + 소셜) | 화면 | `/accounts/login/` | `accounts.views.login_view` (+ `django-allauth`) | `accounts/login.html`, `socialaccount/login.html` | 비로그인 | 정상 |
| P-04 | 로그아웃 | 액션 | `/accounts/logout/` | `accounts.views.logout_view` | - | 로그인 사용자 | 정상 |
| P-05 | 회원 승인 관리 | 화면 | `/accounts/pending-users/...` | `accounts.views.pending_user_list` / `approve_user` / `assign_role` / `reject_user` | `accounts/pending_list.html` | 관리자(`is_staff`) | 정상 |

## 2. 학생

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-06 | 학생 홈 | 화면 | `/student/` | `students.views.student_home` | `student/home.html` | 학생(로그인) | 정상 |
| P-07 | 내 팀 조회 | 화면 | `/student/team/` | `students.views.student_team` | `student/team.html` | 학생(로그인) | 정상 |
| P-08 | 결과 조회 | 화면 | `/student/result/` | `students.views.student_result` | `student/result.html` | 학생(로그인) | 정상 |
| P-09 | 수강생 관리 API | API | `/student/...`(list/update/delete) | `students.views.student_list` / `update_student` / `delete_student` | - (JSON 응답) | 관리자(`is_staff`) | API-Only |

## 3. 팀 편성

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-10 | 회차 관리 | 화면 | `/tutor/rounds/` | `evaluations.views_tutor.round_list` (+ `update_round_status`, `toggle_team_first_rank`) | `tutor/round_list.html` | 관리자(`is_staff`) | 정상 |
| P-11 | 팀 편성 | 화면 | `/tutor/team-build/` | `evaluations.views_tutor.team_build`, `open_team_presentation` | `tutor/team_build.html` | 관리자(`is_staff`) | 정상 |
| P-11a | 팀 편성 API 묶음 | API | `/teams/...` | `teams.views.round_team_members` / `create_team` / `assign_or_move_student` / `get_percentile_preview` / `auto_assign_teams` / `confirm_team_assignment` | - (JSON 응답, `tutor/team_build.html`에서 JS로 호출) | 관리자(생성/수정), 회차 시작 후 조회는 인증 사용자도 가능 | 정상 |

## 4. 평가 (튜터 관리 화면)

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-12 | 팀 평가 현황 | 화면 | `/tutor/team-evaluation/` | `evaluations.views_tutor.team_evaluation` | `tutor/team_evaluation.html` | 관리자(`is_staff`) | **목업**(하드코딩 데이터, DB 미연동) |
| P-13 | 개인 평가 현황 | 화면 | `/tutor/individual-evaluation/` | `evaluations.views_tutor.individual_evaluation` | `tutor/individual_evaluation.html` | 관리자(`is_staff`) | **목업**(하드코딩 데이터, DB 미연동) |
| P-14 | 평가 문항 템플릿 관리 | 화면 | `/tutor/templates/`, `/tutor/templates/new/` | `evaluations.views_tutor.template_list`, `template_create` | `tutor/templates.html`, `tutor/template_form.html` | 관리자(`is_staff`) | 정상 |
| P-15 | 결과 공개 설정 | 화면 | `/tutor/settings/` | `evaluations.views_tutor.tutor_settings` | `tutor/settings.html` | 관리자(`is_staff`) | 정상 |
| P-16 | 평가 현황 대시보드 | 화면 | `/tutor/evaluation-status/` | `evaluations.views_tutor.evaluation_status` | `tutor/evaluation_status.html` | 관리자(`is_staff`) | 정상 |

## 5. 평가 (학생 참여 화면)

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-17 | 팀 평가 목록/작성 | 화면 | `/eval/teams/`, `/eval/teams/<team_id>/` | `evaluations.views_eval.team_evaluation_list`, `team_evaluation_form` | `eval/team_evaluation_list.html`, `eval/team_evaluation_form.html` | 학생(로그인) | 정상 |
| P-18 | 개인(동료) 평가 작성 | 화면 | `/eval/peer/` | `evaluations.views_eval.peer_evaluation_form` | `eval/peer_evaluation_form.html` | 학생(로그인) | 정상 |
| P-19 | 평가 최종 제출 | 액션 | `/eval/submit-final/` | `evaluations.views_eval.submit_final` | - (리다이렉트) | 학생(로그인) | 정상 |

## 미사용 / 중복 구현 (참고용, 정식 프로그램 목록 제외)

| URL | View | Template | 비고 |
|---|---|---|---|
| `/student/evaluation/` | `evaluations.view_eval.evaluation_home` | `student/evaluation.html` (없음) | 템플릿 파일 부재로 호출 시 오류 |
| `/student/evaluation/<round_id>/team/` | `evaluations.view_eval.team_evaluation` | `student/team_evaluation.html` (없음) | 템플릿 파일 부재로 호출 시 오류 |
| `/student/evaluation/<round_id>/individual/` | `evaluations.view_eval.individual_evaluation` | `student/individual_evaluation.html` (없음) | 템플릿 파일 부재로 호출 시 오류 |

또한 `tutor_rounds`, `team_evaluation`, `individual_evaluation` 등 일부 URL 이름이
루트 `urls.py`와 `apps/evaluations/urls.py` 양쪽에 중복 등록되어 있다. `django.urls.reverse()`는
먼저 로드되는 쪽(루트 `urls.py`의 `views_tutor` 직접 연결분)을 사용한다.

## 6. 평가 (예정 — 이번 프로젝트 구현 범위)

| ID | 프로그램명 | 유형 | URL | View | Template | 접근 권한 | 상태 |
|---|---|---|---|---|---|---|---|
| P-20 | 과제 관리 | 화면 | 미정 | 미구현(모델 `Assignment`만 존재, `apps/scoring/admin.py`는 등록 주석 처리됨) | 미구현 | 관리자(`is_staff`) | **예정** |
| P-21 | 튜터 평가 | 화면 | 미정 | 미구현(모델 `TutorEvaluation`만 존재) | 미구현 | 관리자(`is_staff`) | **예정** |
| P-22 | 점수 계산 | 시스템(자동) | - | `apps.scoring.services.calculate_round`, `save_cumulative_seeds`(구현됨, 호출하는 View/트리거 없음) | - | 시스템(회차 종료 시 자동 실행 예정) | **예정** |

이 세 프로그램은 이번 프로젝트 구현 범위에 포함된다(사용자 확정, 2026-08-18). 상세 흐름은
[04_scenarios/11_program_scenario_template.md](../04_scenarios/11_program_scenario_template.md)의 P-20~P-22 참고.
`apps.scoring.services`에 `calculate_round()`/`save_cumulative_seeds()` 계산 로직 자체는 이미 구현돼 있으나,
이를 호출하는 화면/URL/트리거(P-22)가 아직 없다 — 회차 상태를 "종료"로 바꿀 때 자동 호출되도록 연결하는 작업이 남아 있다.

## 7. 프로그램 목록 제외 영역

`apps.results`는 `views.py`/`urls.py`가 비어 있어 별도 프로그램이 없다. 결과 열람은 P-08(결과 조회)이 대신 수행한다.
`apps.students`는 학생 전용 모델 없이 `USER`(role=`STUDENT`)로 대체돼 있다(설계 의도, [02_data/04_table_definition_template.md](../02_data/04_table_definition_template.md) 참고).

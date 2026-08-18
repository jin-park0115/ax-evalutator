# 역할별 권한 매트릭스

## 기본 정보

| 항목 | 내용 |
|---|---|
| 기준 | 각 View의 `@login_required` / `@staff_member_required` 데코레이터, `RoleBasedAuthBackend` |
| 역할 축 | `USER.role`(`PENDING`/`APPROVED`/`STUDENT`/`ADMIN`) × `is_staff` |

## 1. 로그인 가능 여부 (전제 조건)

`RoleBasedAuthBackend`(`apps/accounts/backends.py`)가 비밀번호 일치 여부와 별개로 `role`을 검사한다.

| 역할 | 일반 로그인 | 소셜 로그인 | 비고 |
|---|---|---|---|
| 비로그인(계정 없음) | - | - | 회원가입만 가능(P-02) |
| `PENDING` (승인대기) | 불가 | 불가 | 가입 직후 기본 상태. 관리자 승인 필요 |
| `APPROVED` (역할부여 대기) | 불가 | 불가 | 승인은 됐지만 학생/관리자 역할 미지정 |
| `STUDENT` | 가능 | 가능 | 역할 부여 후 |
| `ADMIN` | 가능 | 가능 | 역할 부여 시 `is_staff=True`도 함께 설정됨 |

즉 `PENDING`/`APPROVED` 계정은 아래 어떤 화면도 실제로는 접근할 수 없다(로그인 단계에서 차단).
아래 표는 "로그인에 성공했다고 가정할 때"의 화면별 접근 권한이다.

## 2. 화면별 접근 권한

| ID | 프로그램명 | 비로그인 | STUDENT | ADMIN(`is_staff`) |
|---|---|---|---|---|
| P-01 | 홈 | R | R | R |
| P-02 | 회원가입 | R/W | - | - |
| P-03 | 로그인 | R/W | - | - |
| P-04 | 로그아웃 | - | W | W |
| P-05 | 회원 승인 관리 | - | - | R/W |
| P-06 | 학생 홈 | - | R | - |
| P-07 | 내 팀 조회 | - | R | - |
| P-08 | 결과 조회 | - | R | - |
| P-09 | 수강생 관리 API | - | - | R/W |
| P-10 | 회차 관리 | - | - | R/W |
| P-11 / P-11a | 팀 편성 (+API) | - | R(회차 시작 후, `round_team_members`만) | R/W |
| P-12 | 팀 평가 현황(목업) | - | - | R |
| P-13 | 개인 평가 현황(목업) | - | - | R |
| P-14 | 평가 문항 템플릿 관리 | - | - | R/W |
| P-15 | 결과 공개 설정 | - | - | R/W |
| P-16 | 평가 현황 대시보드 | - | - | R |
| P-17 | 팀 평가 목록/작성 | - | R/W(본인 제출분만) | - |
| P-18 | 개인(동료) 평가 작성 | - | R/W(본인 제출분만) | - |
| P-19 | 평가 최종 제출 | - | W(본인 제출분만) | - |

R = 조회, W = 생성/수정/삭제, `-` = 접근 불가(코드상 데코레이터 또는 로직으로 차단)

## 3. 세부 제약 사항

| 대상 | 제약 | 근거 |
|---|---|---|
| P-11a `round_team_members` | 회차가 `draft`/`ready`(아직 시작 전) 상태면 `is_staff`만 조회 가능, 그 외 상태는 로그인 사용자 전체 조회 가능 | `teams/views.py`의 `is_round_editable` 분기 |
| P-17 팀 평가 작성 | 자기 팀 평가 불가, 미오픈(`eval_opened_at` 없음) 팀 평가 불가, 최종 제출(`is_final=True`) 후 수정 불가 | [BR-01](../01_requirements/business_rule_BR01.md) |
| P-18 개인 평가 작성 | 자기 자신 평가 불가(팀원 목록에서 본인 제외), 최종 제출 후 수정 불가 | `views_eval.py` `.exclude(student=request.user)` |
| P-19 최종 제출 | 이미 제출한 사용자는 재제출 불가 | `_has_finalized()` 검사 |
| P-08 결과 조회 | 팀 순위/개인 점수/개인 석차는 회차별 공개 플래그가 꺼져 있으면 본인이라도 `None`으로 마스킹 | [BR-10](../01_requirements/business_rule_BR10.md) |
| P-05 역할 부여 | `ADMIN` 지정 시에만 `is_staff=True`로 승격, `STUDENT` 지정 시 `is_staff`는 그대로 `False` | `accounts/views.py` `assign_role` |

## 4. 미구현/확인 필요

- `apps.scoring`, `apps.results`는 화면/API가 없어 권한 정의 대상이 아니다.
- P-09(수강생 관리 API)는 대응 화면 템플릿이 확인되지 않아, 실제로 어떤 프런트에서 호출되는지 별도 확인이 필요하다.

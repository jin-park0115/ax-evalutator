# 설계 검증

## 기본 정보

| 항목 | 내용 |
|---|---|
| 목적 | 요구사항 → 비즈니스 규칙 → 데이터 설계 → 프로그램 설계 → 시나리오 간에 같은 규칙이 같은 의미로 표현되는지 확인한다 |
| 기준 | GitHub Issue "[Docs] 설계 산출물 정합성 및 UI 설계 보완"의 Definition of Done |
| 최근 검증일 | 2026-08-18 (Priority 1 항목) |

## 1. 검증 체크리스트

| # | 항목 | 상태 | 근거 |
|---|---|---|---|
| 1 | 동일 Business Rule이 모든 설계 문서에서 동일하게 표현되어 있다 | ✅ 완료 | BR-02~04(개인평가 규칙)를 [02_data/04_table_definition](../02_data/04_table_definition_template.md), [03_programs/07_program_spec](../03_programs/07_program_spec_template.md)에 교차 인용 |
| 2 | ERD와 테이블 정의서가 일치한다 | ✅ 완료 | [docs/ERD.md](../../ERD.md)를 Deprecated 처리하고 [02_data/03_erd_spec](../02_data/03_erd_spec_template.md)/[04_table_definition](../02_data/04_table_definition_template.md)을 기준 문서로 통일(TEAM_MEMBER N:M 구조) |
| 3 | 데이터 사전과 실제 필드 정의가 일치한다 | ✅ 완료 | [02_data/05_data_dictionary](../02_data/05_data_dictionary_template.md)를 1~5점 스케일 기준으로 재작성, `apps/evaluations/models.py`의 실제 Choices와 일치 확인 |
| 4 | 프로그램 목록과 전체/상세 시나리오의 Program ID가 일치한다 | ✅ 완료 | P-01~P-19(구현됨) + P-20~P-22(예정)를 [03_programs/06_program_list](../03_programs/06_program_list_template.md), [04_scenarios/11_program_scenario](../04_scenarios/11_program_scenario_template.md) 양쪽에 동일하게 반영 |
| 5 | 문항 점수부터 최종점수까지 계산식을 문서만 보고 구현할 수 있다 | ✅ 완료 | [BR-06](../01_requirements/business_rule_BR06.md)/[BR-07](../01_requirements/business_rule_BR07.md)/[BR-08](../01_requirements/business_rule_BR08.md)에 학생·튜터 가중합산 + 절사평균 계산식과 예시 수록(1~5점 스케일 확정) |
| 6 | 최종 제출 가능/불가 조건이 명확하다 | ✅ 완료 | [BR-11](../01_requirements/business_rule_BR11.md) 신설 — 부분 제출 허용을 공식 규칙으로 확정 |
| 7 | 팀 자동편성 Seed 계산 기준이 하나로 정의되어 있다 | ⚠️ 부분 완료 | `apps/scoring/services.py`의 실제 구현(종료 회차 최종점수 평균)과 [BR-09](../01_requirements/business_rule_BR09.md) 서술은 일치하나, Seed "구간(window)" 개념(직전 N회차) 등 UI에 이미 있는 옵션은 아직 BR-09에 반영 안 됨 |
| 8 | 주요 DB 제약조건이 문서화되어 있다 | ⚠️ 부분 완료 | UNIQUE 제약은 [02_data/04_table_definition](../02_data/04_table_definition_template.md)에 문서화됨. `TUTOR_EVALUATION.user_id`/`team_id` 배타 조건(XOR)은 "보완 필요"로만 표시돼 있고 애플리케이션 레벨 검증은 아직 없음 |
| 9 | Requirement → BR → Program → AC → Test까지 추적 가능하다 | ✅ 완료 | [01_requirements/02_traceability_matrix](../01_requirements/02_traceability_matrix_template.md) + [06_test/17_test_case](./17_test_case_template.md)(AC-ID ↔ TC-ID 1:1 매핑) |
| 10 | 주요 화면의 UI Specification과 정적 Mockup을 확인할 수 있다 | ❌ 미완료 | 목업을 따로 만들지 않고 실제 화면을 바로 구현하며 진행함. [15_ui_spec_template.md](../05_ui/15_ui_spec_template.md)도 일부(로그인/홈)만 작성돼 있고 이미지 경로가 깨져 있음. 별도 논의 필요 |
| 11 | 과거 설계와 현재 설계가 혼재되어 있지 않다 | ✅ 완료 | `docs/ERD.md`에 Deprecated 배너로 명시, `docs/templates/` 하위 문서를 기준 문서로 단일화 |

## 2. 결론

Priority 1(계산식/최종제출조건/ERD통일/개인평가규칙)과 Priority 2 대부분(Seed 기준, DB 제약조건, P-20~22 범위)이 반영됐다.
남은 항목은 다음과 같다.

- **Seed "구간(window)" 옵션**을 BR-09에 반영 ([team_build.html](../../../project/templates/tutor/team_build.html)의 "직전 1/3/5회차" 셀렉트가 이미 구현돼 있음)
- **TUTOR_EVALUATION XOR 제약**의 애플리케이션 레벨 검증 추가(문서상 "필요"로만 표시된 상태)
- **UI 명세/목업**은 이번 라운드에서 보류 — 목업 없이 실제 화면으로 바로 개발이 진행된 상태라 별도 결정 필요

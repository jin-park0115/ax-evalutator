# Definition of Done (DoD)

## 기본 정보

| 항목 | 내용 |
|---|---|
| 목적 | "다 됐다"의 기준을 팀 전체가 같게 갖도록 한다 |
| 적용 범위 | 이 프로젝트의 모든 기능 개발/버그 수정 이슈에 공통 적용. 이슈별로 추가 조건은 [20_issue_template.md](./20_issue_template.md)의 "Definition of Done" 섹션에 덧붙인다 |

## 1. 공통 DoD (모든 이슈)

### 기능

- [ ] 이슈에 적힌 요구사항대로 실제로 동작한다(로컬에서 직접 확인)
- [ ] 관련 Business Rule([01_requirements](../01_requirements))을 위반하지 않는다
- [ ] 예외 케이스(권한 없음/빈 값/중복 요청/경계값)가 처리된다

### 코드

- [ ] PR 리뷰([21_review_template.md](./21_review_template.md) 기준)를 통과했다
- [ ] 불필요한 코드 중복/미사용 코드가 없다
- [ ] 마이그레이션이 필요한 모델 변경이면 마이그레이션 파일이 포함돼 있다

### 문서

- [ ] 화면/API/데이터 구조가 바뀌었으면 관련 설계 문서(02_data/03_programs/04_scenarios)를 갱신했다
- [ ] 새 프로그램(화면)이 추가됐으면 [03_programs/06_program_list](../03_programs/06_program_list_template.md)에 반영했다

### 테스트

- [ ] 관련 테스트 케이스([06_test/17_test_case](../06_test/17_test_case_template.md))가 있으면 실행하고 결과를 [18_verification_result](../06_test/18_verification_result_template.md)에 기록했다
- [ ] 없는 경우 새로 추가했다(버그 수정이면 재발 방지용 케이스 포함)

## 2. 설계 문서 정합성 이슈 전용 DoD (참고 예시)

"[Docs] 설계 산출물 정합성 및 UI 설계 보완" 이슈에서 실제로 쓰인 기준. 문서 정리류 이슈를 새로 열 때 참고한다.

- [ ] 동일 Business Rule이 모든 설계 문서에서 동일하게 표현되어 있다
- [ ] ERD와 테이블 정의서가 일치한다
- [ ] 데이터 사전과 실제 필드 정의가 일치한다
- [ ] 프로그램 목록과 전체/상세 시나리오의 Program ID가 일치한다
- [ ] 문항 점수부터 최종점수까지 계산식을 문서만 보고 구현할 수 있다
- [ ] 최종 제출 가능/불가 조건이 명확하다
- [ ] 팀 자동편성 Seed 계산 기준이 하나로 정의되어 있다
- [ ] 주요 DB 제약조건이 문서화되어 있다
- [ ] Requirement → BR → Program → AC → Test까지 추적 가능하다
- [ ] 주요 화면의 UI Specification과 정적 Mockup을 확인할 수 있다
- [ ] 과거 설계와 현재 설계가 혼재되어 있지 않다

이 기준의 현재 충족 여부는 [06_test/16_design_verification_template.md](../06_test/16_design_verification_template.md)에서 추적한다.

## 3. DoD가 아닌 것

- "리뷰어가 보기에 좋아 보인다"는 DoD가 아니다 — 위 체크리스트처럼 **확인 가능한 조건**만 DoD로 인정한다.
- "나중에 고치겠다"는 DoD가 아니다 — 후속 작업이 필요하면 별도 이슈로 분리하고, 그 이슈 번호를 PR에 남긴다.

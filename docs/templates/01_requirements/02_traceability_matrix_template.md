# Traceability Matrix

## 목적

요구사항이 비즈니스 규칙, 개발 기능, 테스트 케이스와
정상적으로 연결되어 있는지 추적하기 위한 문서이다.

---

## 1. 요구사항 추적표

| Requirement ID | 요구사항 | Business Rule | 구현 대상 | Test Case | 담당자 | 상태 |
|---|---|---|---|---|---|---|
| REQ-EVAL-001 | 팀 평가 | BR-01 | TeamEvaluation | TC-EVAL-001 |  |  |
| REQ-EVAL-002 | 개인 평가 대상 제한 | BR-02, BR-03, BR-04 | IndividualEvaluation | TC-EVAL-002 |  |  |
| REQ-EVAL-003 | 평가 중복 방지 | BR-05 | Evaluation | TC-EVAL-003 |  |  |
| REQ-EVAL-004 | 평가 최종 제출(부분 제출 허용) | BR-11 | submit_final(P-19) | TC-EVAL-004 |  |  |
| REQ-SCORE-001 | 팀 점수 계산 | BR-06 | TeamScore | TC-SCORE-001 |  |  |
| REQ-SCORE-002 | 개인 점수 계산 | BR-07 | PersonalScore | TC-SCORE-002 |  |  |
| REQ-SCORE-003 | 최종점수 계산 | BR-08 | FinalScore | TC-SCORE-003 |  |  |
| REQ-TEAM-001 | 자동 팀 편성 | BR-09 | TeamFormation | TC-TEAM-001 |  |  |
| REQ-RANK-001 | 순위 공개 설정 | BR-10 | Ranking / RankingVisibility | TC-RANK-001 |  |  |

---

## 2. Business Rule별 추적

| Rule ID | Business Rule | 관련 Requirement | 구현 대상 | Test Case | 상태 |
|---|---|---|---|---|---|
| BR-01 | 자기 팀 팀 평가 금지 | REQ-EVAL-001 | TeamEvaluation | TC-EVAL-001 |  |
| BR-02 | 다른 팀 개인 구성원 평가 금지 | REQ-EVAL-002 | IndividualEvaluation | TC-EVAL-002 |  |
| BR-03 | 같은 팀 구성원 개인 평가 가능 | REQ-EVAL-002 | IndividualEvaluation | TC-EVAL-002 |  |
| BR-04 | 자기 자신 개인 평가 금지 | REQ-EVAL-002 | IndividualEvaluation | TC-EVAL-002 |  |
| BR-05 | 동일 평가자 중복 평가 금지 | REQ-EVAL-003 | Evaluation | TC-EVAL-003 |  |
| BR-06 | 팀 점수 계산 | REQ-SCORE-001 | TeamScore | TC-SCORE-001 |  |
| BR-07 | 개인 점수 계산 | REQ-SCORE-002 | PersonalScore | TC-SCORE-002 |  |
| BR-08 | 개인 최종점수 계산 | REQ-SCORE-003 | FinalScore | TC-SCORE-003 |  |
| BR-09 | 최종점수의 자동 팀 편성 활용 | REQ-TEAM-001 | TeamFormation | TC-TEAM-001 |  |
| BR-10 | 팀/개인 순위 공개 여부 | REQ-RANK-001 | RankingVisibility | TC-RANK-001 |  |
| BR-11 | 평가 최종 제출 조건(부분 제출 허용) | REQ-EVAL-004 | submit_final(P-19) | TC-EVAL-004 |  |

---

## 3. 추적 관계

```text
Requirement
     ↓
Business Rule
     ↓
Development
     ↓
Test Case
     ↓
Test Result
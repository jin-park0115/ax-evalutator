# ERD 초안

## 주요 엔티티

- `students`: 수강생
- `rounds`: 평가 회차
- `teams`: 회차별 팀
- `team_members`: 팀-수강생 매핑
- `evaluations`: 평가자/대상자/회차별 평가 점수

## 관계

- 한 회차는 여러 팀을 가진다.
- 한 팀은 여러 수강생을 가진다.
- 한 평가는 한 회차, 한 평가자, 한 대상자를 가진다.
- `evaluations(round_id, evaluator_id, target_id)` 조합은 중복될 수 없다.


# 워크플로우 다이어그램

## 기본 정보

| 항목 | 내용 |
|---|---|
| 목적 | 주요 엔티티의 상태 전이와 회차 전체 처리 흐름을 다이어그램으로 정리한다 |
| 연결 문서 | [10_overall_scenario_template.md](./10_overall_scenario_template.md), [02_data/05_data_dictionary_template.md](../02_data/05_data_dictionary_template.md)(코드값 정의) |

---

## 1. 계정(USER) 상태 전이

```mermaid
stateDiagram-v2
    [*] --> PENDING : 회원가입(일반/소셜)
    PENDING --> APPROVED : 관리자 승인
    APPROVED --> STUDENT : 관리자 역할 부여(학생)
    APPROVED --> ADMIN : 관리자 역할 부여(관리자, is_staff=True)
    PENDING --> [*] : 관리자 거절(계정 삭제)
    APPROVED --> [*] : 관리자 거절(계정 삭제)
    STUDENT --> PENDING : 관리자가 목록에서 제외
```

`PENDING`, `APPROVED` 상태에서는 일반 로그인/소셜 로그인 모두 차단된다. `STUDENT`/`ADMIN`으로
역할이 부여된 시점부터 로그인이 가능하다.

---

## 2. 평가 회차(EVALUATION_ROUND) 상태 전이

```mermaid
stateDiagram-v2
    [*] --> draft : 회차 생성
    draft --> ready : 문항/과제/팀 편성 완료 후 확정
    ready --> in_progress : 평가 시작
    in_progress --> finished : 관리자가 회차 종료
    finished --> [*]
```

| 상태 | 의미 | 팀 편성 변경 가능 |
|---|---|---|
| `draft` | 작성 중 | 가능 |
| `ready` | 팀 편성 확정, 시작 대기 | 가능 |
| `in_progress` | 평가 진행 중 | 불가 |
| `finished` | 종료, 점수 계산 완료 | 불가 |

---

## 3. 팀 평가 진행(TEAM.eval_status) 상태 전이

```mermaid
stateDiagram-v2
    [*] --> NOT_OPENED : 팀 생성
    NOT_OPENED --> OPEN : 관리자가 발표 오픈(eval_opened_at 기록)
    OPEN --> CLOSED : 회차 종료 처리
    CLOSED --> [*]
```

발표(평가) 오픈은 팀별로 누적된다 — 나중에 열린 팀이 있어도 먼저 열린 팀은 계속 `OPEN` 상태를 유지한다.

---

## 4. 학생 평가 제출(is_final) 상태 전이

```mermaid
stateDiagram-v2
    [*] --> 임시저장 : 팀 평가 또는 개인 평가 최초 저장(is_final=False)
    임시저장 --> 임시저장 : 재저장(값 덮어쓰기)
    임시저장 --> 최종제출 : 학생이 최종 제출(is_final=True, 회차 단위 일괄 잠금)
    최종제출 --> [*]
```

팀별/문항별 개별 잠금은 없다 — 회차 안에서 학생이 임시저장한 팀 평가·개인 평가 전체가
"최종 제출" 한 번으로 동시에 잠긴다.

---

## 5. 회차 전체 처리 흐름 (관리자 ↔ 학생 ↔ 시스템)

```mermaid
sequenceDiagram
    actor Admin as 관리자
    participant Sys as 시스템
    actor Student as 학생

    Admin->>Sys: 회차 생성 + 문항/과제 등록
    Admin->>Sys: 팀 편성 및 확정 (draft → ready)
    Admin->>Sys: 회차 진행 전환 (ready → in_progress)
    Student->>Sys: 로그인, 과제/팀 확인

    loop 팀별 발표 순서
        Admin->>Sys: 팀 발표(평가) 오픈
        Student->>Sys: 오픈된 팀 평가 작성/수정 (임시저장)
    end

    Student->>Sys: 팀원 개인 평가 작성/수정 (임시저장)
    Admin->>Sys: 튜터 평가 입력 (팀/개인)
    Student->>Sys: 최종 제출 (is_final=True 일괄 잠금)

    Admin->>Sys: 회차 종료 전환 (in_progress → finished)
    Sys->>Sys: 점수 계산 + 석차 산출 + 누적 시드 갱신
    Admin->>Sys: 결과 공개 범위 설정
    Student->>Sys: 결과 조회 (공개된 항목만 노출)
```

---

## 6. 참고

- 상태값의 상세 정의는 [02_data/05_data_dictionary_template.md](../02_data/05_data_dictionary_template.md)의 "1. 코드값" 참고
- 각 단계의 예외 처리는 [12_detailed_scenario_template.md](./12_detailed_scenario_template.md) 참고

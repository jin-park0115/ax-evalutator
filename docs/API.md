# API 초안

## Health

```http
GET /api/health
```

응답:

```json
{
  "status": "ok"
}
```

## 예정 엔드포인트

- `GET /api/students`
- `POST /api/evaluations`
- `GET /api/rounds/{round_id}/teams`
- `POST /api/rounds/{round_id}/teams/assign`
- `GET /api/rounds/{round_id}/scores`
- `POST /api/rounds/{round_id}/results/publish`


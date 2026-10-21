# 로컬 개발 환경

pgvector 확장이 포함된 PostgreSQL을 Docker로 실행합니다.

```bash
cd deploy/local
docker compose up -d
```

- 접속 정보: `postgresql://rag:rag@localhost:5433/rag_portfolio`
- 테이블과 인덱스는 `postgresql/00-init.sql`이 최초 실행 때 만듭니다.
- 데이터까지 모두 지우고 다시 시작하려면 `docker compose down -v` 후 다시 `up` 하세요.

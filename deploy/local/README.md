# 로컬 개발 환경

pgvector 확장이 포함된 PostgreSQL을 Docker로 실행합니다.

```bash
cd deploy/local
docker compose -f docker-compose.yml up -d
```

- 접속 정보: `postgresql://hseungjae:skills53%23@localhost:5433/sjhan`
- 테이블과 인덱스는 `postgresql/00-init.sql`이 최초 실행 때 만듭니다.
- 데이터는 Docker 볼륨(`local_pgdata`)에 저장되므로 Docker를 껐다 켜도 남아 있습니다. 다시 적재할 필요가 없습니다.
- Docker Desktop을 다시 켜도 컨테이너는 자동으로 시작되지 않으니 위 명령을 한 번 실행하세요.
- 데이터까지 모두 지우고 다시 시작하려면 `docker compose down -v` 후 다시 `up` 하고, `projects/system`에서 `python -m scripts.ingest`로 다시 적재하세요.

데이터 유지 여부와 확인 명령어는 [docs/local-guide.md](../../docs/local-guide.md)를 참고하세요.

# 로컬 실행 가이드

로컬에서 챗봇을 띄우고, 데이터를 적재하고, 검색이 잘 되는지 확인하는 방법을 정리했습니다.
명령어는 모두 프로젝트 루트(`RAG-based Portfolio/`)에서 시작한다고 가정합니다.

## 목차

1. 처음 한 번만 하는 준비
2. 매번 실행하는 순서
3. 데이터는 언제 다시 적재해야 하나
4. 확인 명령어
5. 자주 겪는 문제

---

## 1. 처음 한 번만 하는 준비

### 1-1. 필요한 것

| 항목 | 용도 |
|---|---|
| Docker Desktop | pgvector가 들어 있는 PostgreSQL 실행 |
| Node.js 24 + pnpm 10 | React 화면 개발 서버 실행 (`projects/react-app`). pnpm은 `npm install -g pnpm@10.23.0` |
| [uv](https://docs.astral.sh/uv/) | Python 3.12 가상환경과 패키지 설치 |
| Gemini API 키 | 답변 생성과 임베딩 모두 사용 ([AI Studio](https://aistudio.google.com/apikey)에서 무료 발급) |

### 1-2. Python 패키지 설치

```bash
cd projects/system
uv venv -p 3.12
uv pip install -r requirements.txt
```

### 1-3. 환경 변수 설정

```bash
cp projects/system/.env.example projects/system/.env
```

`projects/system/.env`를 열어 값을 채웁니다.

| 변수 | 설명 | 기본값 |
|---|---|---|
| `GEMINI_API_KEY` | Gemini API 키 (필수) | 없음 |
| `DATABASE_URL` | PostgreSQL 접속 주소 | `postgresql://hseungjae:skills53%23@localhost:5433/sjhan` |
| `OWNER_NAME` | 화면과 답변에 쓰이는 이름 | `한승재` |
| `GEMINI_MODEL` | 답변 생성 모델 | `gemini-3.5-flash-lite` |
| `EMBEDDING_MODEL` | 임베딩 모델 | `gemini-embedding-2-preview` |

> `.env`는 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다. API 키는 채팅·이슈·커밋 등 다른 곳에 붙여넣지 마세요.

### 1-4. DB 실행과 최초 적재

```bash
cd deploy/local
docker compose up -d
```

컨테이너가 처음 만들어질 때 `deploy/local/postgresql/00-init.sql`이 실행되어 `vector` 확장, `profile_chunk` 테이블, HNSW 인덱스가 생성됩니다. (지금처럼 청크가 수십 개일 때는 Postgres가 인덱스 대신 순차 스캔을 씁니다. 이유는 [architecture.md](architecture.md) 참고)

```bash
cd projects/system
.venv/bin/python -m scripts.ingest
```

`16개 청크를 저장했습니다.`처럼 나오면 적재가 끝난 것입니다. (개수는 자기소개 문서의 `##` 섹션 수에 따라 달라집니다.)

---

## 2. 매번 실행하는 순서

1. **Docker Desktop을 켭니다.**
2. **DB 컨테이너를 시작합니다.** Docker Desktop을 다시 켜도 컨테이너는 자동으로 시작되지 않습니다.

   ```bash
   cd deploy/local
   docker compose up -d
   ```

3. **서버를 실행합니다.**

   ```bash
   cd projects/system
   .venv/bin/python run.py --reload
   ```

4. **화면(React)을 실행합니다.** 다른 터미널에서 실행하고, 처음 한 번은 `pnpm install`이 필요합니다.

   ```bash
   cd projects/react-app
   pnpm install   # 처음 한 번만
   pnpm dev
   ```

5. 브라우저에서 http://localhost:5173 에 접속합니다. 화면의 `/api` 요청은 Vite가 8000 서버로 넘겨 줍니다.

데이터는 다시 적재하지 않아도 됩니다. 이유는 다음 절을 참고하세요.

---

## 3. 데이터는 언제 다시 적재해야 하나

### 데이터가 저장되는 곳

DB 데이터는 컨테이너 안이 아니라 Docker 볼륨 `local_pgdata`에 저장됩니다.
컨테이너의 `/var/lib/postgresql/data`가 이 볼륨에 연결되어 있어서, 컨테이너를 끄거나 지워도 데이터가 남습니다.

```
deploy/local/docker-compose.yml
  volumes:
    - pgdata:/var/lib/postgresql/data   ← 실제 데이터는 Docker 볼륨에 보관
```

### 동작별 데이터 유지 여부

| 하는 일 | 데이터 | 다시 적재? |
|---|---|---|
| Docker Desktop 종료 후 다시 켜기 | 유지 | 필요 없음 |
| Mac 재부팅 | 유지 | 필요 없음 |
| `docker compose stop` → `start` | 유지 | 필요 없음 |
| `docker compose down` → `up -d` | 유지 (컨테이너만 새로 생성) | 필요 없음 |
| `docker compose down -v` | **삭제** (`-v`가 볼륨까지 지움) | **필요** |

### 다시 적재해야 하는 경우

| 상황 | 이유 |
|---|---|
| `projects/system/dataset/profile/*.md`를 수정했을 때 | DB에는 수정 전 내용의 임베딩이 남아 있음 |
| `EMBEDDING_MODEL`을 바꿨을 때 | 모델이 다르면 문서 벡터와 질문 벡터를 비교할 수 없음 |
| `docker compose down -v`로 볼륨을 지웠을 때 | 테이블이 비어 있음 |

```bash
cd projects/system
.venv/bin/python -m scripts.ingest
```

적재는 매번 테이블을 비우고 전체를 다시 넣는 방식이라, 여러 번 실행해도 데이터가 중복되지 않습니다.
서버를 켠 상태에서 적재해도 되고, 서버를 재시작할 필요도 없습니다.

---

## 4. 확인 명령어

### 4-1. DB 컨테이너가 떠 있는지

```bash
docker ps --filter name=rag-portfolio-postgres
```

`STATUS`가 `Up ...`이면 실행 중입니다.

### 4-2. 데이터가 들어 있는지

```bash
docker exec rag-portfolio-postgres psql -U hseungjae -d sjhan -c "select count(*) as 개수, min(vector_dims(embedding)) as 차원, count(distinct embedding::text) as 서로_다른_벡터 from profile_chunk;"
```

| 값 | 정상 기준 |
|---|---|
| 개수 | 문서의 `##` 섹션 수 (현재 16) |
| 차원 | 1024 (`00-init.sql`의 `vector(1024)`와 같아야 함) |
| 서로_다른_벡터 | 개수와 같아야 함. 작으면 여러 문장이 하나의 벡터로 합쳐진 것 |

### 4-3. 저장된 섹션 목록

```bash
docker exec rag-portfolio-postgres psql -U hseungjae -d sjhan -c "select chunk_id, title from profile_chunk order by chunk_id;"
```

### 4-4. 질문으로 검색 테스트

```bash
cd projects/system
.venv/bin/python -m scripts.search "기능경기대회 성적은?" "지금 어디서 일해요?"
```

```
Q. 지금 어디서 일해요?
  1. (0.58) 한승재는 누구인가 > 경력 (지금 일하는 곳, 현재 직장)
  2. (0.53) 한승재는 누구인가 > 어떤 엔지니어인가
```

- 괄호 안 숫자는 코사인 유사도이고, 1에 가까울수록 질문과 비슷합니다.
- 위에서부터 4개(`settings.top_k`)가 답변 근거로 Gemini에 전달됩니다.
- 원하는 섹션이 4위 안에 없다면, 해당 섹션 제목이나 본문에 질문에 쓰일 만한 표현을 추가한 뒤 다시 적재해 보세요.

### 4-5. 비슷한 섹션끼리 비교

임베딩에 의미가 잘 담겼는지 볼 때 씁니다. 내용이 비슷한 섹션끼리 높게 나오면 정상입니다.

```bash
docker exec rag-portfolio-postgres psql -U hseungjae -d sjhan -c "select a.title, b.title, round((1-(a.embedding<=>b.embedding))::numeric,2) as 유사도 from profile_chunk a join profile_chunk b on a.chunk_id<b.chunk_id order by 3 desc limit 5;"
```

### 4-6. 인덱스를 쓰는지 확인 (실행 계획)

```bash
docker exec rag-portfolio-postgres psql -U hseungjae -d sjhan -c "EXPLAIN SELECT chunk_id FROM profile_chunk ORDER BY embedding <=> (SELECT embedding FROM profile_chunk LIMIT 1) LIMIT 4;"
```

- `Seq Scan` → `Sort`: 전체를 읽어 정렬 (청크가 적을 때 정상)
- `Index Scan using profile_chunk_embedding_idx`: HNSW 인덱스 사용 (청크가 많아지면 이렇게 바뀜)

인덱스가 실제로 몇 번 쓰였는지:

```bash
docker exec rag-portfolio-postgres psql -U hseungjae -d sjhan -c "select indexrelname, idx_scan from pg_stat_user_indexes where relname='profile_chunk';"
```

### 4-7. API로 직접 질문

```bash
curl -N -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"question":"기능경기대회 성적은?"}'
```

`event: sources`(검색된 섹션) → `event: delta`(답변 조각, 여러 번) → `event: done` 순서로 응답이 옵니다.

---

## 5. 자주 겪는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| 서버 시작 시 `Connection refused` | DB 컨테이너가 꺼져 있음 | `cd deploy/local && docker compose up -d` |
| `failed to connect to the docker API` | Docker Desktop이 꺼져 있음 | Docker Desktop 실행 |
| 답변에 수정한 내용이 반영되지 않음 | 문서를 고친 뒤 적재하지 않음 | `.venv/bin/python -m scripts.ingest` |
| "문서 DB에서 검색하지 못했어요" | 테이블이 없거나 DB 연결 실패 | 4-1, 4-2로 확인. 테이블이 없으면 `docker compose down -v && docker compose up -d` 후 다시 적재 |
| "Gemini API 키가 올바르지 않아요" | `.env`의 `GEMINI_API_KEY` 오류 | AI Studio에서 키 확인 후 `.env` 수정, 서버 재시작 |
| "무료 요청을 다 썼거나 요청이 많아요" | Gemini 무료 한도 초과 (429) | 잠시 후 다시 시도. 하루 한도는 AI Studio에서 확인 |
| 답변이 30초 넘게 걸리거나 "AI 서버 응답이 늦어요" | Gemini 무료 플랜이 붐빔 (503 또는 응답 지연) | 503은 자동으로 최대 3번 재시도하고, 60초가 지나면 이 안내를 보여줌. 잠시 후 다시 시도 |
| 모델 호출 시 404 | 신규 키로는 오래된 모델을 쓸 수 없음 | `GEMINI_MODEL`을 사용 가능한 모델로 변경 |
| 포트 5433이 이미 사용 중 | 다른 프로그램이 5433 사용 | `docker-compose.yml`의 `"5433:5432"`와 `.env`의 `DATABASE_URL` 포트를 함께 변경 |

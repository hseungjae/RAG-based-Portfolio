# k3s 배포 (Ubuntu 서버 2대)

Ubuntu 서버 2대로 만든 k3s 클러스터에서 챗봇, DB, Cloudflare Tunnel을 모두 실행합니다.

```
방문자 → https://chat.sjhan.com → Cloudflare → cloudflared 파드 → react-app 서비스(nginx, 80)
                                                                    └─ /api/* → system 서비스(80 → 8000) → postgres(5432)
```

| 노드 | 내부 IP | 역할 |
|---|---|---|
| k3s-1 | 10.0.0.163 | control plane (kubectl, helm 은 여기서) |
| k3s-2 | 10.0.0.135 | agent (워커) |

## 폴더 구조

```
k3s/
├── README.md
├── application/               # 애플리케이션
│   ├── namespace.yaml         #   네임스페이스 rag-portfolio
│   ├── react-app.yaml         #   채팅 화면(nginx) Deployment + Service(ClusterIP 80 → 80)
│   ├── system.yaml            #   챗봇 API 서버 Deployment + Service(ClusterIP 80 → 8000)
│   └── system-ingest-job.yaml #   자기소개 문서 임베딩·적재 Job
├── infra/                     # 인프라
│   ├── database.yaml          #   pgvector PostgreSQL StatefulSet + 헤드리스 Service + 초기 스키마 ConfigMap
│   └── cloudflared.yaml       #   Cloudflare Tunnel Deployment + 설정 ConfigMap
├── cluster/                   # 클러스터 공용 구성 (서비스와 따로 관리)
│   ├── monitoring/            #   모니터링 (kubectl apply -k 로 적용, 7장)
│   │   ├── kustomization.yaml       # 대시보드 JSON 을 ConfigMap 으로 묶음
│   │   ├── namespace.yaml           # 네임스페이스 monitoring
│   │   ├── victoria-metrics.yaml    # 지표 수집·저장 (Prometheus 호환, 15일 보관)
│   │   ├── node-exporter.yaml       # 노드 CPU·메모리·디스크 (DaemonSet)
│   │   ├── kube-state-metrics.yaml  # 파드 상태·재시작·limit
│   │   ├── grafana.yaml             # Grafana + 데이터 소스·대시보드 자동 등록
│   │   └── dashboards/              # 클러스터 자원, API 요청·오류, 질문 통계
│   └── cicd/                  #   배포 자동화 (Jenkins 본체는 직접 설치, 8장)
│       ├── namespace.yaml           # 네임스페이스 jenkins
│       ├── agent-pod.yaml           # 빌드 때만 뜨는 에이전트 파드 (BuildKit, kubectl)
│       └── deployer-rbac.yaml       # 에이전트 권한: rag-portfolio 이미지 교체·롤백·적재 Job
├── sealedsecret/              # Sealed Secrets로 암호화한 시크릿 (커밋해도 안전)
│   ├── system-sealedsecret.yaml       # GEMINI_API_KEY
│   ├── database-sealedsecret.yaml     # POSTGRES_USER/PASSWORD/DB, DATABASE_URL
│   ├── cloudflared-sealedsecret.yaml  # 터널 자격 증명(credentials.json)
│   ├── grafana-sealedsecret.yaml      # Grafana 관리자 비밀번호, DB 읽기 전용 계정
│   └── ghcr-push-sealedsecret.yaml    # GHCR 이미지 push 토큰 (8-1 에서 만듦)
└── sealed-secret.pem          # 봉인용 공개 인증서 (커밋해도 안전)
```

- 시크릿은 클러스터의 sealed-secrets 컨트롤러 공개키로 암호화해 `sealedsecret/`에 둡니다. 컨트롤러가 클러스터 안에서만 풀어 진짜 Secret을 만듭니다.
- 평문 시크릿은 봉인할 때만 `k3s/secrets/`에 잠깐 만들고 지웁니다. 이 폴더는 `.gitignore`로 커밋되지 않습니다.
- 이미지 2개(`system`, `react-app`)는 Jenkins 가 빌드해 GHCR(`ghcr.io/hseungjae/rag-based-portfolio/*`, 공개)에 올리고, 노드는 GHCR 에서 받습니다 (8장).

| 리소스 | 이름 | 사용하는 Secret |
|---|---|---|
| Deployment / Service | `react-app` | - |
| Deployment / Service | `system` | `system-secret`, `database-secret` |
| Job | `system-ingest` | `system-secret`, `database-secret` |
| StatefulSet / Service | `postgres` | `database-secret` |
| Deployment | `cloudflared` | `cloudflared-secret` |
| Deployment / Service | `grafana` (monitoring) | `grafana-secret` |
| Jenkins 본체 (jenkins, 직접 설치) | - | 빌드 에이전트가 `ghcr-push` 사용 |

명령은 모두 k3s-1의 저장소 루트(`~/RAG-based-Portfolio/`)에서 실행한다고 가정합니다.

---

## 1. 처음 한 번만

### 1-1. k3s 클러스터 (2대)

k3s-1 (control plane):

```bash
curl -sfL https://get.k3s.io | sh -s - server --node-ip 10.0.0.163 --disable traefik --write-kubeconfig-mode 644
sudo cat /var/lib/rancher/k3s/server/node-token   # 합류 토큰
```

k3s-2 (agent):

```bash
curl -sfL https://get.k3s.io | K3S_URL=https://10.0.0.163:6443 K3S_TOKEN='<토큰>' sh -s - agent --node-ip 10.0.0.135
```

k3s-1에서 두 노드가 `Ready`인지 확인합니다.

```bash
kubectl get nodes -o wide
```

### 1-2. 저장소, Docker, Helm (k3s-1)

```bash
git clone https://github.com/hseungjae/RAG-based-Portfolio.git && cd RAG-based-Portfolio
sudo apt-get update && sudo apt-get install -y docker.io
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc && export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

### 1-3. Sealed Secrets 컨트롤러와 kubeseal (k3s-1)

```bash
helm repo add sealed-secrets https://bitnami.github.io/sealed-secrets && helm repo update
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system --set fullnameOverride=sealed-secrets-controller
kubectl -n kube-system rollout status deploy/sealed-secrets-controller

VER=$(helm list -n kube-system -f sealed-secrets -o json | grep -o '"app_version":"[^"]*"' | cut -d'"' -f4); VER=${VER#v}
curl -sL "https://github.com/bitnami/sealed-secrets/releases/download/v$VER/kubeseal-$VER-linux-amd64.tar.gz" | tar xz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal && rm kubeseal
```

> **클러스터를 새로 만들면 개인키가 바뀌어** 저장소의 `sealedsecret/`을 풀 수 없습니다. 개인키 백업을 복원하거나(1-4), 4장의 방법으로 다시 봉인하세요.

### 1-4. 개인키 백업 (k3s-1)

```bash
kubectl -n kube-system get secret -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > ~/sealed-secrets-key-backup.yaml
chmod 600 ~/sealed-secrets-key-backup.yaml
```

이 파일은 **절대 GitHub에 올리지 마세요.** 이게 있으면 `sealedsecret/`을 전부 풀 수 있습니다. 새 클러스터에 복원할 때는 컨트롤러를 설치하기 **전에** `kubectl apply -f ~/sealed-secrets-key-backup.yaml`을 먼저 실행합니다.

## 2. 배포

이미지는 Jenkins 가 빌드해 GHCR 에 올립니다(8장). 매니페스트는 GHCR 의 `:latest` 이미지를 받습니다.

적용 순서는 네임스페이스 → 시크릿 → 인프라 → 애플리케이션입니다.

```bash
kubectl apply -f k3s/application/namespace.yaml -f k3s/cluster/monitoring/namespace.yaml
kubectl apply -f k3s/sealedsecret/
kubectl apply -f k3s/infra/
kubectl apply -f k3s/application/
kubectl apply -k k3s/cluster/monitoring/
```

`system-ingest` Job은 DB가 뜰 때까지 몇 번 실패하다가 성공합니다. 확인:

```bash
kubectl -n rag-portfolio get secret              # system-secret, database-secret, cloudflared-secret
kubectl -n rag-portfolio get pods -o wide
kubectl -n rag-portfolio logs job/system-ingest  # "N개 청크를 저장했습니다."
```

브라우저에서 https://chat.sjhan.com 에 접속해 확인합니다.

> Mac에서 같은 터널(`cloudflared tunnel run rag-portfolio`)을 같이 켜 두면 요청이 Mac과 클러스터로 나뉩니다. 클러스터로 옮긴 뒤에는 Mac 쪽 터널을 끄세요.

## 3. 코드 · 문서 수정 후 다시 배포

main 에 push 하면 Jenkins 가 3분 안에 알아채서 **바뀐 이미지만** 빌드·배포합니다. 자기소개 문서(`projects/system/dataset/profile`)가 바뀌었으면 적재 Job 도 다시 돌립니다. 서버에서 따로 할 일은 없습니다.

- 진행 상황: Jenkins 화면(8-3)의 `rag-portfolio` Job
- 새 파드가 5분 안에 준비되지 않으면 Jenkins 가 이전 버전으로 되돌리고 빌드를 실패로 표시합니다.
- 직접 되돌리기: `kubectl -n rag-portfolio rollout undo deployment/system` (react-app 도 같은 방식)
- k3s 매니페스트(`k3s/` 아래 yaml)를 고친 것은 자동 반영되지 않으니 `kubectl apply` 로 직접 적용합니다. 이때 이미지가 `:latest` 로 바뀌지만, Jenkins 가 커밋 태그와 함께 `latest` 도 올리므로 내용은 같습니다.

## 4. 시크릿 값 바꾸기 (다시 봉인)

평문을 `k3s/secrets/`에 잠깐 만들어 봉인하고, 평문은 바로 지웁니다. 예: Gemini 키 교체

```bash
cd k3s && mkdir -p secrets
read -rsp "GEMINI_API_KEY: " KEY && echo
printf 'apiVersion: v1\nkind: Secret\nmetadata:\n  name: system-secret\n  namespace: rag-portfolio\ntype: Opaque\nstringData:\n  GEMINI_API_KEY: "%s"\n' "$KEY" > secrets/system-secret.yaml && unset KEY
kubeseal --cert sealed-secret.pem -oyaml < secrets/system-secret.yaml > sealedsecret/system-sealedsecret.yaml
rm -f secrets/*-secret.yaml
kubectl apply -f sealedsecret/system-sealedsecret.yaml
kubectl -n rag-portfolio rollout restart deployment/system   # envFrom은 파드가 시작할 때만 읽음
```

Secret별 키:

| Secret | 키 |
|---|---|
| `system-secret` | `GEMINI_API_KEY` |
| `database-secret` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` (비밀번호의 `#`은 URL 안에서 `%23`) |
| `cloudflared-secret` | `credentials.json` (Mac의 `~/.cloudflared/<터널ID>.json` 내용) |
| `grafana-secret` | `GF_SECURITY_ADMIN_PASSWORD`, `GRAFANA_DB_NAME`, `GRAFANA_DB_PASSWORD` (7-1 참고) |

다시 봉인한 `sealedsecret/*.yaml`은 커밋해 두면 다음 배포 때 그대로 씁니다.

## 5. 자주 쓰는 명령

| 하는 일 | 명령 |
|---|---|
| 서버 로그 | `kubectl -n rag-portfolio logs -f deploy/system` |
| 화면(nginx) 로그 | `kubectl -n rag-portfolio logs -f deploy/react-app` |
| 터널 로그 | `kubectl -n rag-portfolio logs -f deploy/cloudflared` |
| DB 접속 | `kubectl -n rag-portfolio exec -it postgres-0 -- sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` |
| 서버·터널만 내리기 (DB 유지) | `kubectl -n rag-portfolio scale deploy --all --replicas=0` |
| 다시 올리기 | `kubectl -n rag-portfolio scale deploy --all --replicas=1` |
| DB 데이터까지 전부 삭제 | `kubectl delete namespace rag-portfolio` |
| 모니터링 파드 상태 | `kubectl -n monitoring get pods -o wide` |
| 수집 대상 상태 | `kubectl -n monitoring port-forward svc/victoria-metrics 8428` 후 http://localhost:8428/targets |

## 6. 자원 사용량 (2 vCPU / 4GB / 20GB 기준)

| 구성 | 메모리 | 디스크 |
|---|---|---|
| k3s 자체 | 약 0.5~0.8GB | 약 1GB |
| sealed-secrets 컨트롤러 | 약 50~100Mi | - |
| postgres | 요청 256Mi · 상한 1Gi | PVC 2Gi |
| system | 요청 128Mi · 상한 512Mi | 이미지 약 0.4GB |
| react-app | 요청 16Mi · 상한 64Mi | 이미지 약 0.05GB |
| cloudflared | 요청 64Mi · 상한 256Mi | 이미지 약 0.05GB |
| victoria-metrics | 요청 96Mi · 상한 256Mi | PVC 2Gi |
| grafana | 요청 256Mi · 상한 512Mi | PVC 1Gi |
| kube-state-metrics | 요청 32Mi · 상한 96Mi | - |
| node-exporter (노드마다) | 요청 16Mi · 상한 48Mi | - |
| jenkins 본체 (직접 설치, 권장값) | 요청 768Mi · 상한 1.5Gi | PVC 4Gi 정도 |
| jenkins 빌드 에이전트 (빌드 중에만) | 요청 약 0.8Gi · 상한 약 2.6Gi | 빌드가 끝나면 사라짐 |

- 디스크 20GB 중 OS를 빼면 여유가 크지 않습니다. 이미지는 k3s(containerd)가 GHCR 에서 받아 두고, 디스크가 85%를 넘으면 쓰지 않는 이미지부터 지웁니다. 예전에 수동 빌드하던 Docker 이미지는 `sudo docker image prune -a` 로 지워도 됩니다.
- postgres는 k3s 기본 스토리지(local-path)를 써서 **처음 뜬 노드에 고정**됩니다. 그 노드가 꺼지면 DB도 멈춥니다.

## 7. 모니터링 (Grafana)

```
VictoriaMetrics ──30초마다 수집──▶ node-exporter(노드) · kubelet cAdvisor(컨테이너) · kube-state-metrics(파드 상태) · system /metrics(API)
      │
Grafana ◀─┤  데이터 소스: VictoriaMetrics(지표), PostgreSQL(chat_log 질문 기록, 읽기 전용 계정)
      │
https://grafana.sjhan.com (Cloudflare Tunnel)
```

| 대시보드 | 데이터 | 내용 |
|---|---|---|
| 클러스터 자원 | VictoriaMetrics | 노드 CPU·메모리·디스크, 파드별 메모리·CPU, limit 대비 사용률, 재시작·OOM |
| API 요청·오류 | VictoriaMetrics | 경로·상태 코드별 요청 수, 429, 첫 응답·전체 답변 지연, 답변 결과(ok/error/cancelled) |
| 질문 통계 | PostgreSQL | 질문·방문자 수, 시간대별 질문, 자주 나온 질문, 근거가 부족했던 질문, 실패한 질문, 최근 질문 |

- 대시보드 원본은 `cluster/monitoring/dashboards/*.json`입니다. Grafana 화면에서 고쳐도 저장되지 않으니, 화면에서 고친 뒤 JSON 을 내보내 이 파일을 바꾸고 `kubectl apply -k k3s/cluster/monitoring/` 합니다.
- `/metrics` 는 nginx 가 넘기지 않으므로 외부에서는 볼 수 없습니다.
- 질문 기록(`chat_log`)은 system 이 시작할 때 테이블을 만들고, 답변이 끝날 때마다 한 줄씩 저장합니다. 방문자 IP는 해시만 저장합니다.

### 7-1. 처음 한 번만: DB 읽기 전용 계정과 grafana-secret

새 system 이미지가 한 번 떠서 `chat_log` 테이블이 생긴 뒤에 실행합니다. 비밀번호는 서버에서 만들고 봉인만 커밋합니다.

```bash
cd k3s && mkdir -p secrets
ADMIN_PW=$(openssl rand -base64 24 | tr -d '/+=') DB_PW=$(openssl rand -hex 16)

# grafana_ro: chat_log 만 읽을 수 있는 계정 (여러 번 실행해도 됨)
kubectl -n rag-portfolio exec -i postgres-0 -- sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v db="$POSTGRES_DB" -v pw="$1"' _ "$DB_PW" <<'SQL'
SELECT 'CREATE ROLE grafana_ro LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana_ro')\gexec
ALTER ROLE grafana_ro WITH LOGIN PASSWORD :'pw';
GRANT CONNECT ON DATABASE :"db" TO grafana_ro;
GRANT USAGE ON SCHEMA public TO grafana_ro;
GRANT SELECT ON chat_log TO grafana_ro;
SQL

DB_NAME=$(kubectl -n rag-portfolio get secret database-secret -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)
printf 'apiVersion: v1\nkind: Secret\nmetadata:\n  name: grafana-secret\n  namespace: monitoring\ntype: Opaque\nstringData:\n  GF_SECURITY_ADMIN_PASSWORD: "%s"\n  GRAFANA_DB_NAME: "%s"\n  GRAFANA_DB_PASSWORD: "%s"\n' "$ADMIN_PW" "$DB_NAME" "$DB_PW" > secrets/grafana-secret.yaml
kubeseal --cert sealed-secret.pem -oyaml < secrets/grafana-secret.yaml > sealedsecret/grafana-sealedsecret.yaml
rm -f secrets/grafana-secret.yaml && unset ADMIN_PW DB_PW
kubectl apply -f sealedsecret/grafana-sealedsecret.yaml && cd ..
```

`sealedsecret/grafana-sealedsecret.yaml`은 커밋해 둡니다.

### 7-2. 처음 한 번만: grafana.sjhan.com 연결

Mac(`~/.cloudflared/cert.pem`이 있는 곳)에서 DNS 레코드를 만듭니다. 터널 라우팅은 `infra/cloudflared.yaml`에 이미 들어 있습니다.

```bash
cloudflared tunnel route dns rag-portfolio grafana.sjhan.com
```

Grafana 로그인 화면이 인터넷에 열리므로, Cloudflare 대시보드 **Zero Trust → Access → Applications**에서 `grafana.sjhan.com`에 본인 이메일만 허용하는 정책을 거는 것을 권장합니다 (무료).

### 7-3. 배포와 접속

```bash
kubectl apply -k k3s/cluster/monitoring/
kubectl apply -f k3s/infra/cloudflared.yaml && kubectl -n rag-portfolio rollout restart deployment/cloudflared
kubectl -n monitoring get pods -o wide
```

https://grafana.sjhan.com 에 `hseungjae`(`grafana.yaml`의 `GF_SECURITY_ADMIN_USER`)로 로그인합니다. 비밀번호 확인:

```bash
kubectl -n monitoring get secret grafana-secret -o jsonpath='{.data.GF_SECURITY_ADMIN_PASSWORD}' | base64 -d; echo
```

> 관리자 아이디·비밀번호(`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`)는 Grafana 가 **처음 뜰 때만** 적용되고, 그 뒤로는 Grafana 저장소(PVC)에 있는 값을 씁니다.
> 나중에 바꿀 때는 Grafana 화면(프로필 → Change password, Administration → Users)이나 API 로 계정을 바꾸고, 다음에 새로 설치할 때도 같도록 `grafana.yaml`과 시크릿도 함께 고쳐 둡니다.
> 비밀번호 한 값만 다시 봉인하려면: `printf %s '<새 비밀번호>' | kubeseal --raw --scope strict --name grafana-secret --namespace monitoring --cert k3s/sealed-secret.pem` 결과로 `sealedsecret/grafana-sealedsecret.yaml`의 해당 줄을 바꿉니다.

## 8. 배포 자동화 (Jenkins)

```
git push (main)
  ├─ GitHub Actions: 테스트·lint·빌드 검사 (.github/workflows/ci.yml)
  └─ Jenkins (3분마다 확인, jenkins/Jenkinsfile)
       ├─ 마지막 성공 빌드 이후 바뀐 폴더 확인 (projects/system, projects/react-app, dataset)
       ├─ BuildKit 으로 이미지 빌드 → GHCR push (커밋 해시 태그 + latest, 빌드 캐시도 GHCR)
       ├─ kubectl 로 이미지 교체 → 5분 안에 준비되지 않으면 이전 버전으로 롤백
       └─ 자기소개 문서가 바뀌었으면 적재 Job 다시 실행
```

- 빌드 에이전트는 빌드할 때만 파드로 떴다가 사라집니다. 이미지 빌드를 위해 BuildKit 컨테이너는 privileged 로 돕니다.
- 에이전트 계정(`jenkins-deployer`)은 `rag-portfolio`의 Deployment 이미지 교체·롤백과 적재 Job 실행만 할 수 있습니다.
- Jenkins 는 인터넷에 열지 않고 SSH 터널로만 접속합니다. 그래서 GitHub webhook 대신 3분마다 저장소를 확인합니다.

### 8-1. 처음 한 번만: GHCR 토큰과 ghcr-push 시크릿 (Mac 에서)

1. GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate new token. Scope 는 `write:packages` 만 고릅니다(`read:packages` 가 같이 선택됨).
2. 저장소 루트에서 토큰을 봉인합니다. 토큰은 화면과 셸 기록에 남지 않습니다.

```bash
read -rsp "GHCR 토큰: " GHCR_TOKEN && echo
kubectl create secret docker-registry ghcr-push -n jenkins \
  --docker-server=ghcr.io --docker-username=hseungjae --docker-password="$GHCR_TOKEN" \
  --dry-run=client -o yaml \
  | kubeseal --cert k3s/sealed-secret.pem -oyaml > k3s/sealedsecret/ghcr-push-sealedsecret.yaml
unset GHCR_TOKEN
```

3. `k3s/sealedsecret/ghcr-push-sealedsecret.yaml` 을 커밋·push 합니다. 토큰이 만료되면 같은 방법으로 다시 봉인합니다.

### 8-2. 설치 (k3s-1)

빌드 에이전트가 쓰는 네임스페이스·권한·시크릿을 먼저 만듭니다.

```bash
git pull
kubectl apply -f k3s/cluster/cicd/namespace.yaml
kubectl apply -f k3s/cluster/cicd/deployer-rbac.yaml -f k3s/sealedsecret/ghcr-push-sealedsecret.yaml
kubectl -n jenkins get secret ghcr-push   # 시크릿이 풀렸는지 확인
```

Jenkins 본체는 직접 설치합니다. `jenkins/Jenkinsfile` 이 돌려면 아래가 맞아야 합니다.

| 항목 | 설정 |
|---|---|
| 플러그인 | Pipeline, Git, Kubernetes (단계 화면은 Pipeline Graph View 권장) |
| Kubernetes cloud | 네임스페이스 **`jenkins`** (에이전트 파드가 `jenkins-deployer` 계정과 `ghcr-push` 시크릿을 같은 네임스페이스에서 씀). Jenkins 계정에 이 네임스페이스의 파드 생성·삭제 권한 필요 |
| 본체 executor | 0 (빌드는 에이전트 파드에서만) |
| Job | 이름 `rag-portfolio`, 종류 Pipeline |
| Job → Pipeline | Pipeline script from SCM → Git `https://github.com/hseungjae/RAG-based-Portfolio.git`, 브랜치 `*/main`, Script Path **`jenkins/Jenkinsfile`** |
| Job → Build Triggers | Poll SCM `H/3 * * * *` (3분마다 확인) |

### 8-3. 접속 (Mac 에서 SSH 터널)

```bash
ssh -L 8080:localhost:8080 <k3s-1 SSH 접속 정보> 'kubectl -n jenkins port-forward svc/<Jenkins 서비스 이름> 8080:8080'
```

http://localhost:8080 에 설치할 때 만든 관리자 계정으로 로그인합니다.

### 8-4. 첫 빌드

1. Jenkins 화면에서 `rag-portfolio` → **지금 빌드**(Build Now). 3분마다 확인하는 자동 빌드는 한 번 빌드한 뒤부터 동작합니다.
2. 첫 빌드는 이미지 2개를 모두 빌드합니다. GHCR 패키지는 처음에 **Private** 로 만들어져 노드가 받지 못하므로, Build 단계가 끝나면 GitHub 프로필 → Packages → `rag-based-portfolio/system`, `rag-based-portfolio/react-app` 각각 Package settings → Change visibility → **Public** 으로 바꿉니다.
3. Deploy 단계가 그 전에 실패했다면 이전 버전으로 자동 롤백되어 서비스는 그대로입니다. Public 으로 바꾼 뒤 다시 **지금 빌드** 를 누릅니다.

| 하는 일 | 명령 |
|---|---|
| 지금 배포된 이미지 태그 | `kubectl -n rag-portfolio get deploy -o wide` |
| Jenkins·빌드 에이전트 파드 상태 | `kubectl -n jenkins get pods -o wide` |
| 지금 도는 빌드 에이전트의 BuildKit 로그 | `kubectl -n jenkins logs -f <에이전트 파드> -c buildkit` |

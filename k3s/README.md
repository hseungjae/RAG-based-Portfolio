# k3s 배포 (Ubuntu 서버 2대)

Ubuntu 서버 2대로 만든 k3s 클러스터에서 챗봇, DB, Cloudflare Tunnel을 모두 실행합니다.

```
방문자 → https://chat.sjhan.com → Cloudflare → cloudflared 파드 → react-app 서비스(nginx, 80)
                                                                    └─ /api/* → system 서비스(80 → 8000) → postgres(5432)
```

| 노드 | 내부 IP | 역할 |
|---|---|---|
| k3s-1 | 10.0.0.163 | control plane (kubectl, helm, 이미지 빌드는 여기서) |
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
├── monitoring/                # 모니터링 (kubectl apply -k 로 적용, 7장)
│   ├── kustomization.yaml     #   대시보드 JSON 을 ConfigMap 으로 묶음
│   ├── namespace.yaml         #   네임스페이스 monitoring
│   ├── victoria-metrics.yaml  #   지표 수집·저장 (Prometheus 호환, 15일 보관)
│   ├── node-exporter.yaml     #   노드 CPU·메모리·디스크 (DaemonSet)
│   ├── kube-state-metrics.yaml#   파드 상태·재시작·limit
│   ├── grafana.yaml           #   Grafana + 데이터 소스·대시보드 자동 등록
│   └── dashboards/            #   클러스터 자원, API 요청·오류, 질문 통계
├── sealedsecret/              # Sealed Secrets로 암호화한 시크릿 (커밋해도 안전)
│   ├── system-sealedsecret.yaml       # GEMINI_API_KEY
│   ├── database-sealedsecret.yaml     # POSTGRES_USER/PASSWORD/DB, DATABASE_URL
│   ├── cloudflared-sealedsecret.yaml  # 터널 자격 증명(credentials.json)
│   └── grafana-sealedsecret.yaml      # Grafana 관리자 비밀번호, DB 읽기 전용 계정
└── sealed-secret.pem          # 봉인용 공개 인증서 (커밋해도 안전)
```

- 시크릿은 클러스터의 sealed-secrets 컨트롤러 공개키로 암호화해 `sealedsecret/`에 둡니다. 컨트롤러가 클러스터 안에서만 풀어 진짜 Secret을 만듭니다.
- 평문 시크릿은 봉인할 때만 `k3s/secrets/`에 잠깐 만들고 지웁니다. 이 폴더는 `.gitignore`로 커밋되지 않습니다.
- 이미지 2개(`system`, `react-app`)를 k3s-1에서 직접 빌드해 **두 노드 모두에** 넣습니다(레지스트리 없음, `imagePullPolicy: Never`).

| 리소스 | 이름 | 사용하는 Secret |
|---|---|---|
| Deployment / Service | `react-app` | - |
| Deployment / Service | `system` | `system-secret`, `database-secret` |
| Job | `system-ingest` | `system-secret`, `database-secret` |
| StatefulSet / Service | `postgres` | `database-secret` |
| Deployment | `cloudflared` | `cloudflared-secret` |
| Deployment / Service | `grafana` (monitoring) | `grafana-secret` |

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

## 2. 이미지 빌드 · 배포

이미지 2개를 빌드해 k3s-1에 넣고, k3s-2에도 보냅니다.

```bash
sudo docker build -t system:latest projects/system
sudo docker build -t react-app:latest projects/react-app
sudo docker save system:latest react-app:latest -o ~/rag-portfolio.tar && sudo chown $USER ~/rag-portfolio.tar
sudo k3s ctr images import ~/rag-portfolio.tar
scp ~/rag-portfolio.tar ubuntu@10.0.0.135:~ && ssh -t ubuntu@10.0.0.135 'sudo k3s ctr images import ~/rag-portfolio.tar && rm ~/rag-portfolio.tar'
rm ~/rag-portfolio.tar
```

> 파드가 이미지 없는 노드에 배정되면 `ErrImageNeverPull`로 뜨지 않으니, 반드시 두 노드 모두에 넣습니다.

적용 순서는 네임스페이스 → 시크릿 → 인프라 → 애플리케이션입니다.

```bash
kubectl apply -f k3s/application/namespace.yaml -f k3s/monitoring/namespace.yaml
kubectl apply -f k3s/sealedsecret/
kubectl apply -f k3s/infra/
kubectl apply -f k3s/application/
kubectl apply -k k3s/monitoring/
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

```bash
git pull
# 2장의 "이미지 빌드 · 두 노드 import" 명령 실행
kubectl -n rag-portfolio rollout restart deployment/system deployment/react-app
sudo docker image prune -f   # 이전 이미지 정리 (디스크 절약)
```

자기소개 문서(`projects/system/dataset/profile`)를 고쳤다면 적재도 다시 합니다.

```bash
kubectl -n rag-portfolio delete job system-ingest --ignore-not-found
kubectl apply -f k3s/application/system-ingest-job.yaml
```

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

- 디스크 20GB 중 OS를 빼면 여유가 크지 않으니, 빌드 후 `sudo docker image prune -f`로 이전 이미지를 지웁니다. 이미지가 Docker와 k3s(containerd)에 한 벌씩 저장되기 때문입니다.
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

- 대시보드 원본은 `monitoring/dashboards/*.json`입니다. Grafana 화면에서 고쳐도 저장되지 않으니, 화면에서 고친 뒤 JSON 을 내보내 이 파일을 바꾸고 `kubectl apply -k k3s/monitoring/` 합니다.
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
kubectl apply -k k3s/monitoring/
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

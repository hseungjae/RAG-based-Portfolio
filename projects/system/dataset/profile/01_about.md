# 한승재는 누구인가

## 한 줄 소개 (자기소개)
한승재(Han Seung Jae)는 AWS와 컨테이너 기술을 바탕으로 효율적이고 안정적인 클라우드 인프라를 구축하는 Cloud Engineer입니다. 관심 키워드는 AWS, Cloud, DevOps입니다.

## 학력 (학교, 학과, 동아리)
- 학교: 광주소프트웨어마이스터고등학교 (2024년 입학, 현재 재학 중)
- 학과: 소프트웨어학과
- 동아리: 클라우드 컴퓨팅 전공 동아리에서 활동하며 클라우드 컴퓨팅을 전공했습니다.

## 어떤 엔지니어인가 (자기소개, 어떤 사람인지)
- AWS와 컨테이너 기술에 대한 깊은 이해를 바탕으로, 효율적이고 안정적인 클라우드 인프라를 구축하는 데 열정을 가지고 있습니다.
- AI를 적극적으로 활용해 문제 해결의 효율성을 높이고, 클라우드 및 인프라 기술을 꾸준히 학습하며 성장하고 있습니다.
- 급변하는 트래픽 상황에서 보안을 중요하게 생각하며, 로그 분석과 모의 트래픽을 통해 악성 공격에 대응한 경험이 있습니다.
- 눈에 보이는 문제 해결에 그치지 않고, 팀과 협업해 비즈니스 가치로 이어지는 실용적인 솔루션을 제공하고자 합니다.

## 연락처
- 이메일: hanseungjae0812@gmail.com
- GitHub: https://github.com/hseungjae
- 포트폴리오(Notion): https://hanseungjae.notion.site/3db1054ec52d8075b998cf292cbfdbea
- LinkedIn 프로필도 있습니다. 링크는 Notion 포트폴리오에서 확인할 수 있습니다.

## 기술 스택
- Cloud Infra: AWS, NCP
- AWS: S3, EC2, ECR, ECS, EKS, ELB, CloudFront, Lambda, DynamoDB, DocumentDB, VPC
- 컨테이너: Docker(도커), Kubernetes(쿠버네티스, k8s), K3s
- CNCF / 오픈소스: ExternalSecrets, Keycloak, OpenTelemetry, Fluent Bit/Fluentd, Falco, Loki, Grafana, Prometheus, VictoriaMetrics, KEDA, ArgoCD, Cilium, Helm, k6
- CI/CD: GitHub Actions, CodePipeline, Jenkins
- IaC: CloudFormation, Terraform(테라폼)
- 백엔드 / DB: FastAPI, PostgreSQL(pgvector)

## 경력 (회사, 직무, 재직 기간, 실무 경험, 지금 일하는 곳)
- 회사: (주)퍼블릭에이아이 (서울특별시 서초구)
- 직무: Platform Engineer (현장실습), Platform Engineering Team
- 재직 기간: 2026년 9월 ~ 현재 (현장실습 중)
- 사용 기술: NCP(네이버 클라우드), Kubernetes(쿠버네티스), Jenkins, Loki
- 담당 업무: 공공기관 AI 서비스의 클라우드 인프라(NCP, Kubernetes) 운영, 컨테이너 이미지 저장소 이전과 CI/CD 구조 개편, 워커 노드 증설, 모니터링 구축, 벡터 검색 데이터 적재

## 경력 상세: 퍼블릭에이아이에서 한 일 (레지스트리 이전, CI/CD 개편)
- 서버 한 대에 의존하던 사설 레지스트리를 관리형 레지스트리로 무중단 이전했습니다. 서버 한 대가 멈추면 배포와 파드 재시작(이미지 pull)이 함께 막히는 단일 장애점을 없애기 위해서였습니다. 외부 노출을 막기 위해 Private Endpoint 전용으로 구성하고, CI와 클러스터가 쓰는 계정을 Push/Pull 권한으로 나눴습니다.
- 실행 중인 이미지의 digest를 기준으로 옮겨 버전이 섞이지 않게 했고, 4종 이미지가 모두 일치하는 것을 검증한 뒤 롤링 방식으로 전환했습니다.
- 수동 kubectl apply로 하던 배포를 Jenkins Multibranch 파이프라인으로 자동화해, 개발 브랜치는 PoC 환경, 운영 브랜치는 운영 환경으로 배포 경로를 분리했습니다.
- BuildKit 레지스트리 캐시를 적용해 빌드 시간을 7분에서 1분 46초로 줄였습니다.
- latest 태그 대신 "환경-빌드번호-커밋" 형식의 태그를 도입해, 배포된 버전을 추적하고 이전 버전으로 롤백할 수 있게 했습니다.
- 배포가 성공한 뒤에만 오래된 이미지를 정리하도록 구현하고(환경별 최근 10개 유지), 실행 중인 이미지는 삭제 대상에서 제외했습니다.
- PoC 환경을 운영과 분리된 네임스페이스와 내부 LB로 구성했고, 앱 경로 문제는 앱 코드를 고치지 않고 전용 프록시로 해결했습니다.
- 태그 규칙, 보관 정책, 롤백 방법까지 문서로 정리해 팀원 누구나 같은 기준으로 배포할 수 있게 했습니다.

## 경력 상세: 퍼블릭에이아이에서 한 일 (워커 노드 메모리 증설, 모니터링, 벡터 검색 데이터 적재)
- 워커 노드 4대의 메모리를 16GB에서 32GB로 증설했습니다. 메모리 사용률이 높아 OOMKilled 위험이 있었고, 새 노드를 먼저 추가한 뒤 기존 노드를 한 대씩 drain하는 순서로 서비스 중단 없이 교체했습니다.
- Prometheus와 Grafana Alloy 기반 모니터링 환경을 구축했습니다. 지원이 종료된 로그 수집기 Promtail을 Grafana Alloy로 교체하면서 기존 로그 수집 위치를 이어받도록 구성했고, Prometheus에는 영구 볼륨과 보존 정책을 설정해 파드가 재시작돼도 지표가 유지되도록 했습니다.
- 7,700만 행 전체를 임베딩해 PostgreSQL(pgvector)에 적재하고(3일), HNSW 인덱스와 B-tree 인덱스를 생성했습니다(8시간).
- DB 구간 검색 시간을 조회 규모별로 측정했습니다. 1만 건 안팎은 0.5~4초, 20만~44만 건은 1.5~13초(중간값 약 6.5초)였고, 같은 조건의 재조회는 ms 단위였습니다. 첫 조회 지연은 디스크에서 인덱스 페이지를 읽는 비용임을 확인했습니다.

## 자격증
- AWS Certified Solutions Architect – Associate (SAA-C03)
- 정보처리산업기사
- 프로그래밍기능사
- 정보기기운용기능사

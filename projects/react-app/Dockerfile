# 1단계: Node 이미지로 빌드
FROM node:24-alpine AS build

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일을 복사하고 설치
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# pnpm 은 package.json 의 packageManager 필드와 같은 버전으로 고정한다.
# 버전을 비워 두면 그날의 최신 pnpm 이 설치되어 lockfile 과 맞지 않을 수 있다.
RUN npm install -g pnpm@10.23.0
RUN pnpm install --frozen-lockfile

# 소스 코드 복사
COPY . .

# Vite를 사용해 빌드
RUN pnpm run build

# 2단계: Nginx 이미지를 사용해 빌드된 파일을 제공
#   docker build -t react-app:latest projects/react-app
FROM nginx:1.29-alpine

# Nginx 설정 파일 복사
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# 빌드된 파일을 Nginx의 기본 정적 파일 제공 경로로 복사
COPY --from=build /app/dist /usr/share/nginx/html

# 컨테이너가 80 포트에서 실행되도록 설정
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]

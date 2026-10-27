FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 빌드 컨텍스트는 projects/ 다 — settings.web_dir 이 system 의 형제 폴더(web)를 가리키므로 구조를 그대로 둔다.
#   docker build -f projects/system/Dockerfile -t rag-portfolio:latest projects
WORKDIR /app/system
COPY system/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY system/ /app/system/
COPY web/ /app/web/

RUN useradd --system --uid 10001 app
USER 10001

EXPOSE 8000
CMD ["python", "run.py"]

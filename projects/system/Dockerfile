FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 화면은 projects/react-app 이미지가 따로 제공하므로, 이 이미지에는 API 서버만 넣는다.
#   docker build -t system:latest projects/system
WORKDIR /app/system
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/system/

RUN useradd --system --uid 10001 app
USER 10001

EXPOSE 8000
CMD ["python", "run.py"]

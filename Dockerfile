# 법정 증거 이메일 처리 시스템 - 공식 이미지
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="Email Evidence Processor Team"
LABEL version="2.0.0"
LABEL description="한국 법원 제출용 이메일 증거 처리 시스템"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
  wkhtmltopdf \
  curl \
  fontconfig \
  fonts-nanum \
  fonts-nanum-coding \
  fonts-nanum-extra \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 폰트 캐시 업데이트
RUN fc-cache -fv

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# 추가 의존성 (psutil 등)
RUN pip install --no-cache-dir psutil

# 애플리케이션 소스 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p /app/data \
  /app/processed_emails \
  /app/logs \
  /app/reports \
  /app/temp \
  /app/uploads \
  /app/static \
  /app/templates

# 권한 설정
RUN chmod +x start_web.py \
  && chmod +x main.py \
  && chown -R nobody:nogroup /app

# 포트 노출
EXPOSE 5000

# 헬스체크 스크립트 추가
COPY docker-healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD /usr/local/bin/docker-healthcheck.sh

# 비특권 사용자로 실행
USER nobody

# 환경변수 설정
ENV PYTHONPATH=/app
ENV FLASK_APP=start_web.py
ENV FLASK_ENV=production

# 애플리케이션 실행
CMD ["python", "start_web.py"]

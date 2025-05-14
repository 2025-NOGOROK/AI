# 1. 베이스 이미지 선택
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app
ENV FLASK_APP=nogorok.py

# 3. 필요한 파일 복사 (의존성 먼저 → 빌드 캐시 활용)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 4. 소스 코드 및 데이터 파일 복사
COPY nogorok.py short.csv ./

# 5. 서버 실행 (포트 통일)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

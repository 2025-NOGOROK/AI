# 1. 베이스 이미지 선택
FROM python:3.10


# 2. 작업 디렉토리 지정
WORKDIR /app
ENV FLASK_APP=nogorok.py
# 3. 소스코드 복사
COPY . /app

# 4. 의존성 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. Flask 앱 실행 (포트 5000 예시, 필요시 0.0.0.0으로 바꿔야 외부접속 가능)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

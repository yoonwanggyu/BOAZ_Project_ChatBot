FROM python:3.9

WORKDIR /app

# 환경 변수 파일을 컨테이너로 복사
COPY .env .env

# 필요한 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# chatbot_logic.py 파일을 컨테이너로 복사
COPY chatbot_logic.py ./

# 스트림릿 앱 파일도 복사
COPY streamlit_app.py ./

# .env 파일을 로드하고 스트림릿 앱 실행
CMD ["bash", "-c", "source .env && streamlit run streamlit_app.py"]
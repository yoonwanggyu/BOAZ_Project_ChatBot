import os
from dotenv import load_dotenv
import streamlit as st
from chatbot_logic import initialize_conversation, initialize_pinecone  # 챗봇 로직 파일에서 불러오기

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# streamlit 설정
st.set_page_config(page_title="FinanceChat", page_icon=":books:")
st.title(":blue[Card Chatbot] :books:")

# 사이드바에 디버그 모드 설정 추가
debug_mode = st.sidebar.checkbox("디버그 모드", value=False)

# Pinecone 설정
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = initialize_pinecone()

# 대화 기록 초기화
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role': 'assistant', 'content': "안녕하세요! 무엇이 궁금하신가요?"}]

# Streamlit app logic
if 'conversation' not in st.session_state:
    st.session_state.conversation = initialize_conversation(st.session_state.vectorstore)

# 사용자 입력 받기
prompt = st.chat_input("질문을 입력해주세요.")

# chat logic
if prompt:
    st.session_state['messages'].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # 대화 모델 호출
        result = st.session_state.conversation.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": "session123"}}  # 예시 세션 ID 사용
        )

        # LLM의 응답 추출
        full_response = result.get("answer", "Sorry, no answer was generated.")
        message_placeholder.markdown(full_response)

        # 디버그 모드가 활성화된 경우 참조된 문서 표시
        if debug_mode:
            st.write("### 참조된 문서들:")
            st.write(result)

        # 디버그 모드에서도 대화가 기록되도록 메시지 추가
        st.session_state['messages'].append({"role": "assistant", "content": full_response})

import os
from dotenv import load_dotenv
import streamlit as st
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from chatbot_logic import initialize_conversation  # 챗봇 로직 파일에서 불러오기

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# streamlit
st.set_page_config(page_title="FinanceChat", page_icon=":books:")
st.title(":blue[Card Chatbot] :books:")

# 채팅 화면을 구현한 코드
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role': 'assistant',
                                    'content': "안녕하세요! 무엇이 궁금하신가요?"}]

# 대화 기록 표시
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Pinecone 인스턴스 및 VectorStore 초기화 (한 번만 실행)
if 'vectorstore' not in st.session_state:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "card-chatbot"

    # 인덱스 가져오기
    index = pc.Index(index_name)

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'}
    )

    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")
    st.session_state.vectorstore = vectorstore

# 대화 객체 초기화 (한 번만 실행)
if 'conversation' not in st.session_state:
    st.session_state.conversation = initialize_conversation(st.session_state.vectorstore)
    print("init completed")

# 사용자 입력 받기
prompt = st.chat_input("질문을 입력해주세요.")

# chat logic
if prompt:
    st.session_state['messages'].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        result = st.session_state.conversation.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": "session123"}}  # 예시 세션 ID 사용
        )

        # 필요한 데이터 추출 및 표시
        full_response = result.get("answer", "Sorry, no answer was generated.")
        message_placeholder.markdown(full_response)

    st.session_state['messages'].append({"role": "assistant", "content": full_response})

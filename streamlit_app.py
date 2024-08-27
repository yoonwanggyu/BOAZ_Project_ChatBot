import os
from dotenv import load_dotenv
import streamlit as st
from chatbot_logic import initialize_conversation, initialize_pinecone  # 챗봇 로직 파일에서 불러오기

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# streamlit 설정
st.set_page_config(page_title="FinanceChat", page_icon=":books:", layout="centered")
st.title("💳 **Card Chatbot**")

# 사이드바에 디버그 모드 설정 추가
st.sidebar.title("Settings")
debug_mode = st.sidebar.checkbox("🛠️ 디버그 모드", value=False)

# Pinecone 설정
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = initialize_pinecone()

# 대화 기록 초기화
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role': 'assistant', 'content': "안녕하세요! 무엇이 궁금하신가요?"}]

# Streamlit app logic
if 'conversation' not in st.session_state:
    st.session_state.conversation = initialize_conversation(st.session_state.vectorstore)

# 이전 대화 기록 표시
st.subheader("💬 대화 기록")
chat_container = st.container()
with chat_container:
    for message in st.session_state['messages']:
        role = "🙋 User" if message['role'] == "user" else "🤖 Assistant"
        st.markdown(f"**{role}:** {message['content']}")

# 사용자 입력 받기
st.divider()
input_container = st.container()
with input_container:
    prompt = st.text_input("💬 질문을 입력해주세요:", placeholder="카드 혜택을 알고 싶으신가요? 여기에 질문을 입력하세요...")

# chat logic
if prompt:
    st.session_state['messages'].append({"role": "user", "content": prompt})

    with chat_container:
        st.markdown(f"**🙋 User:** {prompt}")

    with chat_container:
        message_placeholder = st.empty()

        # 스피너 추가 - 답변 생성 중
        with st.spinner("답변 생성 중..."):
            result = st.session_state.conversation.invoke(
                {"input": prompt},
                config={"configurable": {"session_id": "session123"}}  # 예시 세션 ID 사용
            )

        # LLM의 응답 추출
        full_response = result.get("answer", "Sorry, no answer was generated.")
        message_placeholder.markdown(f"**🤖 Assistant:** {full_response}")

        # 디버그 모드가 활성화된 경우 참조된 문서 표시
        if debug_mode:
            with st.expander("🔍 참조된 문서들"):
                docs = result.get("context", [])
                if docs:
                    st.write("**참조된 문서 리스트:**")
                    for idx, doc in enumerate(docs):
                        card_name = doc.metadata.get('card_name', 'N/A')
                        company = doc.metadata.get('company', 'N/A')
                        benefit = doc.metadata.get('benefit', 'N/A')
                        content = doc.page_content
                        st.markdown(
                            f"""
                            <div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;'>
                                <strong>📄 문서 {idx + 1}</strong><br>
                                <strong>카드 이름:</strong> {card_name}<br>
                                <strong>회사:</strong> {company}<br>
                                <strong>혜택:</strong> {benefit}<br>
                                <strong>내용:</strong> {content}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.write("No documents found.")

    # 디버그 모드에서도 대화가 기록되도록 메시지 추가
    st.session_state['messages'].append({"role": "assistant", "content": full_response})

# 스타일 추가 (기본 스타일 유지, 심플하게)
st.markdown(
    """
    <style>
    .stTextInput, .stAlert {
        border-radius: 10px;
    }
    .css-1gkdjib.e1yohnl3 {
        height: 70vh;
        overflow-y: auto;
    }
    .css-1gkdjib.e1yohnl3 > div {
        margin-bottom: 10px;
    }
    .css-145kmo2.e1ewe7hr3 {
        margin-top: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import os
from dotenv import load_dotenv
import streamlit as st
from pinecone import Pinecone
from langchain_community.llms import Ollama

from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers.self_query.base import SelfQueryRetriever

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 임베딩 모델 차원 확인 (예: BAAI/bge-m3는 1024차원)
EMBEDDING_DIMENSION = 1024  # 모델에 맞게 차원 설정

def load_model():
    model = Ollama(model="gemma2:2b")
    print("model loaded...")
    return model 

def rag_chain(vectorstore):
    llm = Ollama(model='gemma2')
    
    metadata_field_info = [
    AttributeInfo(name='company',
                  description='The card company written on the card_name',
                  type='string'),
    AttributeInfo(name='card_name',
                  description='The name of the card held by the company',
                  type='string'),
    AttributeInfo(name='benefit',
                  description='The name of the benefits you can receive when using the card listed on card_name',
                  type='string')]

    document_content_description = "Explanation of the benefits offered by a total of 10 cards"

    self_query_retriever = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        document_content_description,
        metadata_field_info,
    )

    system_prompty = """When there is prior conversation history and a new user question, the question might be related to the previous conversation. 
    Use the documents you retrieved in response to the previous question to answer the new question.
    """
    
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system",system_prompty),
        MessagesPlaceholder("chat_history"),
        ("human","{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm,
        self_query_retriever,
        contextualize_prompt
    )

    qa_system_prompt = """Your are an assistant helping with question-answering tasks. 
    Use the retrieved information to answer the questions. 
    If the information includes details like card_name or specific benefits, make sure to include them in your answer. 
    If you do not know the answer, simply say you don't know. 
    Please provide the answers in Korean.

    {context}"""

    qa_prompt = ChatPromptTemplate.from_messages([
    ("system",qa_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human","{input}"),
    ])

    qa_chain = qa_prompt | llm | StrOutputParser()

    rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

    return rag_chain

# streamlit
st.set_page_config(page_title="FinanceChat",
                       page_icon=":books:")
st.title(":blue[Card Chat]_ :books:")

# 채팅 화면을 구현한 코드
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role' : 'assistant',
                                    'content' : "안녕하세요! 무엇이 궁금하신가요?"}]
    
# 대화 기록 표시
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Pinecone 인스턴스 및 VectorStore 초기화 (한 번만 실행)
if 'vectorstore' not in st.session_state:
    # Pinecone 인스턴스 생성 및 초기화
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "card-chatbot"

    # 인덱스 가져오기
    index = pc.Index(index_name)

    # PineconeVectorStore를 사용하여 벡터 스토어 생성
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'}
    )

    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")
    st.session_state.vectorstore = vectorstore

# 대화 객체 초기화 (한 번만 실행)
if 'conversation' not in st.session_state:
    st.session_state.conversation = rag_chain(st.session_state.vectorstore)
    print("init completed")

# 사용자 입력 받기
prompt = st.chat_input("질문을 입력해주세요.")

# chat logic
if prompt:
    st.session_state['messages'].append({"role":"user","content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        result = st.session_state.conversation.invoke({"input":prompt,"chat_history":st.session_state['messages']})

        # Debugging line to check what is inside `result`
        st.write("Debugging result:", result)  # This line will print the structure of `result`
        
        # 필요한 데이터 추출 및 표시
        full_response = result.get("answer", "Sorry, no answer was generated.")
        message_placeholder.markdown(full_response)

    st.session_state['messages'].append({"role":"assistant","content":full_response})

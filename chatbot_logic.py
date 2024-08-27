import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 임베딩 모델 차원 확인 (예: BAAI/bge-m3는 1024차원)
EMBEDDING_DIMENSION = 1024  # 모델에 맞게 차원 설정

def load_model():
    model = ChatOpenAI(
        temperature=0.1,
        model_name="gpt-4",  # GPT-4 모델 사용
        streaming=True
    )
    print("model loaded...")
    return model 

def rag_chain(vectorstore):
    llm = load_model()
    
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

    qa_system_prompt = """You are an assistant helping with question-answering tasks. 
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

    return create_retrieval_chain(history_aware_retriever, qa_chain)

# 세션 기록을 저장할 딕셔너리
store = {}

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids):
    if session_ids not in store:  # 세션 ID가 store에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 store에 저장
        store[session_ids] = ChatMessageHistory()
    return store[session_ids]  # 해당 세션 ID에 대한 세션 기록 반환

def initialize_conversation(vectorstore):
    base_rag_chain = rag_chain(vectorstore)
    
    return RunnableWithMessageHistory(
        base_rag_chain,
        get_session_history,
        input_messages_key="input",  # 사용자의 질문이 템플릿 변수에 들어갈 key
        history_messages_key="chat_history",  # 기록 메시지의 키
        output_messages_key="answer",
    )

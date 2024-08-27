import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_history_aware_retriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_community.document_transformers import LongContextReorder
from langchain_pinecone import PineconeVectorStore

from operator import itemgetter

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pinecone 설정
def initialize_pinecone():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "card-chatbot"

    # 인덱스 가져오기
    index = pc.Index(index_name)

    # HuggingFace 임베딩 로드
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'}
    )

    # Pinecone VectorStore 생성
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")
    return vectorstore

def load_model():
    model = ChatOpenAI(
        temperature=0.1,
        model_name="gpt-4o-mini",
        streaming=True
    )
    print("model loaded...")
    return model 

def rag_chain(vectorstore):
    llm = load_model()

    # 리트리버 설정
    model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
    compressor_15 = CrossEncoderReranker(model=model, top_n=15)
    vs_retriever30 = vectorstore.as_retriever(search_kwargs={"k": 30})
    retriever = ContextualCompressionRetriever(base_compressor=compressor_15, base_retriever=vs_retriever30)
    
    # 리트리버 파이프라인
    system_prompty = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Please answer the question with new retrieved context, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompty),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever_modified = create_history_aware_retriever(
        llm,
        retriever,
        contextualize_prompt
    )

    # 문서 재정렬 추가
    reordering = LongContextReorder()

    my_retriever = (
        {"input": itemgetter("input"),
         "chat_history": itemgetter("chat_history")
        } | history_aware_retriever_modified | 
        RunnableLambda(lambda docs: reordering.transform_documents(docs))
    )
    
    # LLM 체인 설정
    qa_system_prompt = """You are an assistant helping with question-answering tasks. 
    Use the retrieved information to answer the questions. 
    If the information includes details like card_name or specific benefits, make sure to include them in your answer. 
    If you do not know the answer, simply say you don't know. 
    Please provide the answers in Korean.

    {context}"""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # RAG 체인 생성
    return create_retrieval_chain(my_retriever, question_answer_chain)

# 세션 기록을 저장할 딕셔너리
store = {}

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids):
    if session_ids not in store:  # 세션 ID가 store에 없는 경우
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

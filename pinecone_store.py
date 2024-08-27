import os
from dotenv import load_dotenv
import json
import time
from tqdm import tqdm
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

# .env 파일에서 환경 변수 로드
load_dotenv()

# 필요한 환경 변수 불러오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# 임베딩 모델 차원 확인 (예: BAAI/bge-m3는 1024차원)
EMBEDDING_DIMENSION = 1024  # 모델에 맞게 차원 설정

def load_documents(data_path):
    documents = []

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for company_name, company_data in data.items():
        for card in company_data['cards']:
            for benefit, details in card['benefits'].items():
                metadata = {
                    'company': company_name,
                    'card_name': card['name'],
                    'benefit': benefit
                }
                page_content = card['summary'] + "\n" + "\n".join(details)
                documents.append(Document(metadata=metadata, page_content=page_content))

    return documents

def create_embeddings_and_db(documents):
    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, 
                                                   chunk_overlap=100,
                                                   length_function=len)
    split_docs = text_splitter.split_documents(documents)

    # Hugging Face 임베딩 생성
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'}
    )

    # Pinecone 인스턴스 생성 및 초기화
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "card-chatbot"
    
    # 인덱스가 이미 존재하는 경우 생성하지 않고 사용
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name, 
            dimension=EMBEDDING_DIMENSION,  # 임베딩의 차원을 설정 (BAAI/bge-m3 임베딩의 차원)
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        # 인덱스가 준비될 때까지 대기
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    # 인덱스 가져오기
    index = pc.Index(index_name)

    # PineconeVectorStore를 사용하여 벡터 스토어 생성
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")

    # 문서에 UUID 할당
    uuids = [str(uuid4()) for _ in range(len(split_docs))]

    # 벡터 스토어에 문서 추가 (진행 상황 표시)
    for doc, uuid in tqdm(zip(split_docs, uuids), total=len(split_docs), desc="Pinecone에 문서 추가 중"):
        vectorstore.add_documents(documents=[doc], ids=[uuid])

    print("문서 저장이 완료되었습니다.")
    return vectorstore

if __name__ == "__main__":
    data_path = "combined_card_info.json"
    documents = load_documents(data_path)
    create_embeddings_and_db(documents)

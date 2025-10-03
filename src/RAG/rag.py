# RAG/rag.py
import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

load_dotenv()

def run_rag_pipeline(pdf_path: str):
    # 1. Cargar documento
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # 2. Dividir en chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    # 3. Embeddings
    embedding_model = OpenAIEmbeddings(model='text-embedding-ada-002')

    # 4. Supabase Vector Store
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    client = create_client(supabase_url, supabase_key)

    # Tabla y query dedicadas para O&G compliance
    vectorstore = SupabaseVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        client=client,
        table_name="documents_oag_compliance",
        query_name="match_documents_oag_compliance",
    )

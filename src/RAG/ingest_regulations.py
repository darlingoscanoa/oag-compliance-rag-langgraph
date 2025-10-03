# RAG/ingest_regulations.py
"""
Admin-only script to pre-populate Supabase with regulatory PDFs.
- Scans the RAG/Regulations directory (or a custom path).
- Loads each PDF, splits into chunks, assigns metadata (corpus='regulations'),
  and upserts into the existing Supabase vector table used by the app.

Usage:
  python -m RAG.ingest_regulations  # uses default directory 'RAG/Regulations'
  python -m RAG.ingest_regulations --dir /path/to/pdfs

Requires environment variables:
  SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
"""
import argparse
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client
from langchain.schema import Document

load_dotenv()

DEFAULT_DIR = "RAG/Regulations"
TABLE_NAME = "documents_oag_compliance"          # same table as app ingestion
QUERY_NAME = "match_documents_oag_compliance"     # same RPC as app ingestion


def _collect_pdfs(directory: str) -> List[Path]:
    base = Path(directory)
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])


def _load_and_chunk(pdf_path: Path) -> List[Document]:
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    # Ensure minimal, consistent chunking with the app
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # Attach regulation-specific metadata
    for idx, d in enumerate(chunks):
        d.metadata = {
            **(d.metadata or {}),
            "corpus": "regulations",
            "source_pdf": pdf_path.name,
            "source_path": str(pdf_path),
            "chunk_index": idx,
        }
    return chunks


def ingest_regulations(directory: str = DEFAULT_DIR) -> None:
    pdfs = _collect_pdfs(directory)
    if not pdfs:
        print(f"[ingest] No PDF files found in '{directory}'.")
        return

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment.")

    client = create_client(supabase_url, supabase_key)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    total_chunks = 0
    for pdf in pdfs:
        print(f"[ingest] Processing: {pdf.name}")
        chunks = _load_and_chunk(pdf)
        if not chunks:
            print(f"[ingest] Skipped (no content): {pdf.name}")
            continue

        SupabaseVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=client,
            table_name=TABLE_NAME,
            query_name=QUERY_NAME,
        )
        total_chunks += len(chunks)
        print(f"[ingest] Upserted {len(chunks)} chunks from {pdf.name}")

    print(f"[ingest] Completed. Total chunks upserted: {total_chunks}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest regulatory PDFs into Supabase vector store.")
    parser.add_argument("--dir", dest="directory", default=DEFAULT_DIR, help="Directory containing PDF regulations")
    args = parser.parse_args()
    ingest_regulations(args.directory)

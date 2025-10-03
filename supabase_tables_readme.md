# Supabase setup (documents_oag_compliance)

This project uses a single table and RPC in Supabase to store and query embeddings for O&G compliance RAG. The SQL mirrors the professor's template, only changing the table/function names to match the code in `src/RAG/rag.py`.

- Table: `documents_oag_compliance`
- Function: `match_documents_oag_compliance`
- Embedding dim: `1536` (OpenAI `text-embedding-ada-002`)

## 1) Enable extension
```sql
-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;
```

## 2) Create table
```sql
-- Create the table to store your documents
-- Names match the Python script
create table documents_oag_compliance (
  id uuid primary key default gen_random_uuid(),
  content text,
  metadata jsonb,
  -- 1536 dimensions because we use 'text-embedding-ada-002'
  embedding vector (1536)
);
```

## 3) Create similarity match function (CORRECTED)
```sql
-- Drop existing function if any to avoid conflicts
DROP FUNCTION IF EXISTS match_documents_oag_compliance(vector(1536), int, jsonb);

-- Create the corrected function with explicit table references
-- This fixes the "column reference 'id' is ambiguous" error
CREATE OR REPLACE FUNCTION match_documents_oag_compliance(
  query_embedding vector(1536),
  match_count int DEFAULT 5,
  filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents_oag_compliance.id,
    documents_oag_compliance.content,
    documents_oag_compliance.metadata,
    1 - (documents_oag_compliance.embedding <=> query_embedding) AS similarity
  FROM documents_oag_compliance
  WHERE (filter = '{}'::jsonb OR documents_oag_compliance.metadata @> filter)
  ORDER BY documents_oag_compliance.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

> Tip: If you later get errors about `id` being null on insert, you can alter the table to add a default: `alter table documents_oag_compliance alter column id set default gen_random_uuid();` and enable `pgcrypto` extension.

## 4) Environment variables
Create a `.env` file (not committed) with the following:
```
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...   # used by the admin-only ingestion script
OPENAI_API_KEY=...
# App keys (optional): if you want the Streamlit app to be read-only, use anon key there
SUPABASE_ANON_KEY=...
```

## 5) Admin-only ingestion (preload regulations)
Place regulatory PDFs under `src/RAG/Regulations/`, then run:
```
cd oag-compliance-rag-langgraph/src
python -m RAG.ingest_regulations
# or with a custom folder
python -m RAG.ingest_regulations --dir "/path/to/regulations"
```
The script will chunk PDFs and upsert into `documents_oag_compliance` using the service key.

## 6) App ingestion (user uploads)
The Streamlit app (`src/streamlit_app.py`) uploads a PDF, does a relevance filter (`Yes/No`), and if relevant, calls `run_rag_pipeline()` to ingest that PDF into the same table.

- Code reference: `src/RAG/rag.py`
  - `table_name="documents_oag_compliance"`
  - `query_name="match_documents_oag_compliance"`

## 7) Quick test (verify function works)
After you have at least one row, test the RPC:
```sql
-- Test with an actual embedding from your table
SELECT * FROM match_documents_oag_compliance(
  (SELECT embedding FROM documents_oag_compliance LIMIT 1),
  5,
  '{}'::jsonb  -- no filter
);

-- Test with corpus filter (used by the app)
SELECT * FROM match_documents_oag_compliance(
  (SELECT embedding FROM documents_oag_compliance LIMIT 1),
  5,
  '{"corpus": "regulations"}'::jsonb
);
```
Alternatively, use the Python SDK to call the RPC from a notebook or script.

## 8) Permissions (optional minimal guidance)
If you require read-only app access and admin-only writes:
- Use `SUPABASE_ANON_KEY` in the Streamlit app for reads.
- Use `SUPABASE_SERVICE_KEY` only in `RAG/ingest_regulations.py` for writes.
- Configure RLS policies to allow `select` for anon and `all` for service_role on `documents_oag_compliance`.

This keeps the current code and naming intact while enabling others to replicate your setup quickly.

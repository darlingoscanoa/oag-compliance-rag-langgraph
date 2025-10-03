# graph.py
"""
- Define tools
- Define task agents (ReAct)
- Build supervisor workflow = create_supervisor(...)
- Compile workflow for Studio multi-node diagram
- Keep app = filter_agent as your single-agent entry
"""
import os
import json
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from supabase import create_client

load_dotenv()

# Model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ---------------- Agent 1 — Filter (no tools) ----------------
filter_agent = create_react_agent(
    model=model,
    name="filter_agent",
    tools=[],
    prompt="""
You are an expert in Oil & Gas regulatory compliance in Canada.
Classify if the user's text is potentially relevant to compliance topics:
- emissions (methane/VOC), LDAR
- venting/flaring
- spills/effluents/water
- monitoring/reporting

Respond ONLY 'Yes' or 'No' with no explanation.
"""
)

# ---------------- Base Tools ----------------
@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Web search (Tavily). Returns JSON with title/url/content."""
    try:
        from tavily import TavilyClient
    except Exception:
        return json.dumps({"error": "tavily package missing (pip install tavily-python)"})
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "Missing TAVILY_API_KEY"})
    client = TavilyClient(api_key=api_key)
    resp = client.search(query=query, max_results=max_results)
    return json.dumps(resp or {})

@tool
def match_regulations(query: str, match_count: int = 5) -> str:
    """Semantic search over Supabase 'regulations' corpus (RPC). Returns JSON rows."""
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vector = embeddings.embed_query(query)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    client = create_client(supabase_url, supabase_key)

    payload = {
        "query_embedding": vector,
        "match_count": match_count,
        "filter": {"corpus": "regulations"}
    }
    resp = client.rpc("match_documents_oag_compliance", payload).execute()
    return json.dumps(resp.data or [])

# ---------------- Agents 2–5 ----------------

# 2) Web Search agent (uses Tavily tool)
web_search_agent = create_react_agent(
    model=model,
    name="web_search_agent",
    tools=[web_search],
    prompt="""
You search the public web for supplemental context (guidance, definitions, recent notes).
When useful, call web_search and provide concise, cited pointers. Otherwise answer briefly.
"""
)

# 3) Compliance Retriever agent (uses Supabase RPC tool)
compliance_retriever_agent = create_react_agent(
    model=model,
    name="compliance_retriever_agent",
    tools=[match_regulations],
    prompt="""
You retrieve regulatory passages relevant to Oil & Gas compliance.
When asked for clauses/citations, call match_regulations, return concise results with references.
Otherwise answer briefly.
"""
)

# 4) Gap Analyzer agent (no tools)
gap_analyzer_agent = create_react_agent(
    model=model,
    name="gap_analyzer_agent",
    tools=[],
    prompt="""
Analyze conversation context that includes:
- internal document excerpts
- regulatory snippets retrieved previously

Output a compact bullet list of potential gaps with a short rationale and severity (Low/Medium/High).
If context is insufficient, state so briefly. Do not call tools.
"""
)

# 5) Report/Summary agent (no tools)
report_generator_agent = create_react_agent(
    model=model,
    name="report_generator_agent",
    tools=[],
    prompt="""
Generate a concise triage report using only conversation context:
- One-paragraph executive summary
- Bullet list of flagged gaps (if any)
- 2–3 recommended next actions
Do not call any tools. Keep it business-friendly and brief.
"""
)

# ---------------- Supervisor Workflow (LangGraph-2025-2 style) ----------------
workflow = create_supervisor(
    agents=[
        compliance_retriever_agent,   # retrieve clauses
        gap_analyzer_agent,           # analyze gaps
        report_generator_agent,       # summarize and next actions
        web_search_agent,             # public web context
    ],
    model=model,
    prompt="""
You are a supervisor/router for an Oil & Gas compliance triage workflow.
Decide which agent to run next based on the goal and conversation data:
- compliance_retriever_agent: retrieve clauses/citations from the regulations DB.
- gap_analyzer_agent: compare the user's excerpts vs retrieved clauses and list gaps with severity.
- report_generator_agent: produce an executive summary and actionable next steps.
- web_search_agent: fetch recent public context and cite links if relevant.
Always move the task forward and stop when the user's goal is satisfied.
"""
)

# Compile for Studio multi-node diagram (like LangGraph-2025-2)
demo_app = workflow.compile()
# Alias for minimal manifest (single entry: graph:agent)
agent = demo_app

# ---------------- Exports ----------------
# Keep single-agent Yes/No entry (if you want to demo it separately later)
app = filter_agent


# Utility function for Streamlit app
def evaluate_document_theme(text: str) -> str:
    """Filter agent: returns 'Yes' or 'No' for compliance relevance."""
    state = {"messages": [HumanMessage(content=text)]}
    res = filter_agent.invoke(state)
    return res["messages"][-1].content

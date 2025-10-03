# Oil & Gas Compliance RAG System with Multi-Agent LangGraph

[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Cloud](https://img.shields.io/badge/cloud-GCP-orange)](https://cloud.google.com/)

**Multi-agent RAG system for Oil & Gas compliance gap analysis using LangGraph supervisor orchestration.** Features specialized agents (retriever, analyzer, reporter) with Supabase pgvector, Gemini 2.5, and production deployment on GCP Cloud Run.

🔗 **[Read the Full Story on LinkedIn](https://www.linkedin.com/pulse/from-architecture-production-building-enterprise-ai-system-oscanoa-olufe/)**

---

## 🎯 The Problem

The oil and gas industry has accumulated **$56.8 billion** in environmental violation penalties since 2000. In Canada, operators face fines from **$25,000 to $12 million** per violation under new emissions regulations. Most failures aren't intentional—they're the result of information overload and the impossibility of humans keeping pace with evolving regulations.

**This system transforms compliance from a reactive burden into a proactive advantage.**

---

## ✨ Key Features

- **🤖 Multi-Agent Architecture**: Supervisor orchestrates specialized agents (Filter, Retriever, Gap Analyzer, Report Generator, Web Search)
- **📚 RAG Foundation**: 1,607 regulatory chunks from SOR/2018-66 and AER Directive 060 in Supabase pgvector
- **⚡ Intelligent Filtering**: Rejects non-compliance documents before processing (40% cost reduction)
- **📊 Semantic Search**: Sub-100ms similarity search with metadata filtering
- **🎨 Streamlit UI**: User-friendly interface for PDF upload and instant analysis
- **🔍 Full Observability**: LangGraph Studio + LangSmith tracing + GCP Cloud Logging
- **🐳 Production-Ready**: Docker containerization with non-root user, health checks, and GCP Cloud Run deployment
- **💰 Cost-Optimized**: ~$8/month serverless deployment vs $75 for always-on VMs

---

## 🏗️ Architecture
┌─────────────┐ │ User │ └──────┬──────┘ │ Upload PDF ▼ ┌─────────────────────────────────────┐ │ Streamlit UI │ └──────┬──────────────────────────────┘ │ ▼ ┌─────────────────────────────────────┐ │ Filter Agent (Classification) │ │ ✓ Compliance-relevant? Yes/No │ └──────┬──────────────────────────────┘ │ If Yes ▼ ┌─────────────────────────────────────┐ │ RAG Ingestion Pipeline │ │ → Chunk → Embed → Store Supabase │ └──────┬──────────────────────────────┘ │ ▼ ┌─────────────────────────────────────┐ │ Supervisor Agent (LangGraph) │ │ Routes to specialized agents │ └──────┬──────────────────────────────┘ │ ├──→ Compliance Retriever Agent │ (Semantic search regulations) │ ├──→ Gap Analyzer Agent │ (Compare doc vs regulations) │ ├──→ Report Generator Agent │ (Executive summary + actions) │ └──→ Web Search Agent (Recent guidance & context)


---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker (for deployment)
- Google Cloud account (optional, for production)
- API Keys:
  - [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini)
  - [OpenAI](https://platform.openai.com/api-keys) (embeddings)
  - [Tavily](https://tavily.com/) (web search)
  - [Supabase](https://supabase.com/) (vector store)
  - [LangSmith](https://smith.langchain.com/settings) (optional, tracing)

### Local Development

```bash
# Clone repository
git clone [https://github.com/darlingoscanoa/oag-compliance-rag-langgraph.git](https://github.com/darlingoscanoa/oag-compliance-rag-langgraph.git)
cd oag-compliance-rag-langgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.sample .env
cp src/.env.sample src/.env
# Edit both .env files with your API keys

# Setup Supabase (follow instructions in supabase_tables_readme.md)
# 1. Create table: documents_oag_compliance
# 2. Create RPC function: match_documents_oag_compliance
# 3. Ingest regulations: python -m RAG.ingest_regulations

# Run Streamlit app
streamlit run src/streamlit_app.py
LangGraph Studio (Multi-Agent Visualization)
bash
# Install LangGraph CLI
pip install langgraph-cli

# Run from src/ directory
cd src
langgraph dev --allow-blocking

# Open Studio UI in browser (link shown in terminal)
🐳 Docker Deployment
Build and Run Locally
bash
# Build production image
docker build -f Dockerfile.prod -t oag-compliance:latest .

# Run container
docker run -p 4000:4000 \
  -e GOOGLE_API_KEY="your_key" \
  -e OPENAI_API_KEY="your_key" \
  -e SUPABASE_URL="your_url" \
  -e SUPABASE_SERVICE_KEY="your_key" \
  -e TAVILY_API_KEY="your_key" \
  oag-compliance:latest
Deploy to Google Cloud Run
bash
# Copy sample files and configure
cp COMMANDS.md.sample COMMANDS.md
cp cloudbuild.yaml.sample cloudbuild.yaml
cp service.yaml.sample service.yaml
# Edit files with your GCP project details

# Build and deploy
gcloud builds submit --config=cloudbuild.yaml
gcloud run services replace service.yaml --region us-central1
📊 Production Results
Scenario 1: Compliant Document ✅
Input: Inspection report with quarterly LDAR surveys, low-bleed devices, VRU installed

Output:

✅ LDAR Program: Quarterly surveys completed (SOR/2018-66, Section 6)
✅ Pneumatic Devices: All low-bleed (<6 scf/hr) (SOR/2018-66, Section 8)
✅ Venting/Flaring: VRU installed, <100 m³/month (AER Directive 060)
✅ Water Management: Closed-loop system, licensed disposal
✅ Documentation: Current ERP, trained staff

Conclusion: Operations meet regulatory requirements. Continue current practices.
Impact: Instant audit-ready documentation, proactive verification before inspections

Scenario 2: Critical Gaps Identified ⚠️
Input: Inspection report with overdue LDAR, high-bleed devices, excessive venting

Output:

Gap 1: LDAR Survey Overdue (HIGH)
Regulation: SOR/2018-66, Section 6 - Requires quarterly surveys
Rationale: Last survey October 2023 (18 months ago). Facility 15 months overdue.

Gap 2: Prohibited High-Bleed Pneumatic Devices (HIGH)
Regulation: SOR/2018-66, Section 8(1) - Prohibits devices >6 scf/hr after Jan 2023
Rationale: 12 high-bleed controllers operating. All must be replaced.

Gap 3: Excessive Venting Without Flare (HIGH)
Regulation: AER Directive 060, Section 3.2 - Requires flare for >500 m³/month
Rationale: Facility vents 1,200 m³/month. Immediate flare installation required.

Recommended Actions:
1. Schedule LDAR survey within 30 days
2. Replace high-bleed devices by Q1 2026
3. Install flare system by Q2 2026
Impact: Each violation = $25K-$500K in potential fines. Early detection enables remediation before AER inspection.

Scenario 3: Intelligent Filtering 🚫
Input: "WorldCup_Final_2022_Summary.pdf"

Output:

Filter result: No
Message: Document does not appear relevant for Oil & Gas compliance.
Impact: Saves ~$0.15 per rejected document. At 10,000 docs/month, saves $18,000 annually.

🧪 Testing
bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
📁 Project Structure
oag-compliance-rag-langgraph/
├── src/
│   ├── graph.py                    # Multi-agent workflow (LangGraph)
│   ├── streamlit_app.py            # Streamlit UI
│   ├── langgraph.json              # LangGraph Studio config
│   ├── RAG/
│   │   ├── rag.py                  # RAG ingestion pipeline
│   │   ├── ingest_regulations.py  # Preload regulations
│   │   ├── KnowledgeBase/         # User-uploaded documents
│   │   └── Regulations/           # Regulatory PDFs
│   └── .env                        # Environment variables (gitignored)
├── tests/
│   ├── test_filter_agent.py       # Filter agent tests
│   ├── test_rag_pipeline.py       # RAG pipeline tests
│   └── test_streamlit_app.py      # Streamlit tests
├── Dockerfile.prod                 # Production Docker image
├── cloudbuild.yaml.sample          # GCP Cloud Build config
├── service.yaml.sample             # GCP Cloud Run service
├── requirements.txt                # Python dependencies
├── supabase_tables_readme.md       # Supabase setup guide
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
🔧 Tech Stack
Component	Technology	Purpose
LLM	Google Gemini 2.5 Flash	Agent reasoning & text generation
Orchestration	LangGraph	Multi-agent workflow & state management
Embeddings	OpenAI text-embedding-ada-002	Document & query vectorization
Vector DB	Supabase (pgvector)	Semantic search over regulations
Web Search	Tavily API	Recent guidance & public context
Frontend	Streamlit	User interface
Deployment	Docker + GCP Cloud Run	Serverless container hosting
Observability	LangSmith + GCP Logging	Agent tracing & monitoring
💰 Cost Analysis
Cloud API Costs (Current)
Per-document processing: ~$0.21 (embeddings + LLM)
Monthly (1,000 docs): ~$210
Annual: ~$2,520
Cloud Run hosting: ~$8/month
Enterprise Scale (10,000 docs/month)
Cloud APIs: $25,200/year
On-premise GPU (4× NVIDIA L40S): $120K upfront, $530K saved over 5 years
Breakeven: Month 18
Recommendation: Start with cloud for MVP, migrate to hybrid architecture at scale.

🔐 Security Best Practices
✅ Non-root Docker user (UID 1000)
✅ Health checks for orchestration
✅ Secrets via environment variables (never hardcoded)
✅ 
.gitignore
 protects API keys
✅ Sample configs for safe sharing
✅ GCP Secret Manager integration (production)
📈 Future Enhancements
 Production monitoring dashboards (Grafana + Prometheus)
 Model fine-tuning on company-specific compliance data
 Edge deployment for remote sites with intermittent connectivity
 A/B testing framework for prompt optimization
 Multi-language support (French for Quebec operations)
 Integration with existing ERP systems
🤝 Contributing
Contributions welcome! Please:

Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit changes (git commit -m 'Add amazing feature')
Push to branch (git push origin feature/amazing-feature)
Open a Pull Request
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

👤 Author
Darling Oscanoa
AI Solutions Architect & ML Engineer

LinkedIn: linkedin.com/in/darlingoscanoa
GitHub: @darlingoscanoa
Article: From Architecture to Production: Building an Enterprise AI Compliance System
🙏 Acknowledgments
Canadian regulatory frameworks: SOR/2018-66, AER Directive 060
LangChain & LangGraph teams for excellent multi-agent tooling
Supabase for pgvector integration
Google AI Studio for Gemini API access
📞 Questions?
Have questions about:

Multi-agent architecture patterns?
RAG implementation strategies?
Production deployment best practices?
Cost optimization at scale?
Open an issue or connect on LinkedIn - I'm happy to help!

⭐ If this project helped you, please star the repository!
# streamlit_app.py
import streamlit as st
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage
from graph import evaluate_document_theme, agent  # Import the supervisor workflow
from RAG.rag import run_rag_pipeline

# Use English folder names for consistency
UPLOAD_DIR = "RAG/KnowledgeBase"
REGULATIONS_DIR = "RAG/Regulations"  # place regulatory PDFs here (preloaded corpus)

# Ensure base folders exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REGULATIONS_DIR, exist_ok=True)

st.title("Oil & Gas Compliance Triage (Canada)")
st.write("Upload a PDF to analyze whether it is relevant for compliance verification (methane/VOC, LDAR, venting/flaring, discharges/effluents, reporting).")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    # Clean the KnowledgeBase folder
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save uploaded file
    pdf_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract text for initial filtering
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    full_text = "\n".join([doc.page_content for doc in documents])

    st.info("Analyzing document relevance for Oil & Gas compliance...")
    result = evaluate_document_theme(full_text)
    st.write(f"Filter agent result: **{result}**")

    if "yes" in result.lower():
        st.success("The document is potentially relevant. Running ingestion pipeline to Supabase (RAG)...")
        run_rag_pipeline(pdf_path)
        st.success("✅ Document processed and stored in Supabase for future RAG queries.")
        
        # NEW: Run the multi-agent compliance analysis
        st.info("🔍 Running compliance gap analysis...")
        
        # Prepare the analysis request
        analysis_prompt = f"""
        Analyze this inspection report for Oil & Gas compliance:
        
        Document: {uploaded_file.name}
        
        CRITICAL: You MUST output the FULL DETAILED REPORT in your final response. Do not just say "analysis complete".
        
        Instructions:
        1. Retrieve relevant regulatory clauses from SOR/2018-66 (federal methane regulations) and AER Directive 060 (Alberta flaring/venting).
        2. Compare document against regulations and identify gaps with:
           - Specific regulation citation (e.g., "SOR/2018-66, Section 8(1)")
           - Severity (Low/Medium/High)
           - Brief rationale
        3. If NO significant gaps: provide SHORT compliance checklist (3-5 categories with ✅).
        4. If gaps found: YOU MUST provide the COMPLETE detailed report with:
           - Executive summary paragraph
           - Each gap listed with:
             * Gap title
             * Regulation citation
             * Severity level
             * Detailed rationale
           - 2-3 recommended corrective actions
        
        Document excerpt (first 2000 chars):
        {full_text[:2000]}
        
        EXAMPLE FORMAT FOR COMPLIANT DOCUMENTS:
        **Compliance Status: COMPLIANT ✅**
        
        - ✅ LDAR Program: Quarterly surveys completed (SOR/2018-66, Section 6)
        - ✅ Pneumatic Devices: All low-bleed or instrument air (SOR/2018-66, Section 8)
        - ✅ Venting/Flaring: VRU installed, <100 m³/month (AER Directive 060)
        - ✅ Water Management: Closed-loop system, licensed disposal (AER Directive 086)
        - ✅ Documentation: Current ERP, trained staff
        
        **Conclusion**: Operations meet regulatory requirements. Continue current practices.
        
        EXAMPLE FORMAT FOR NON-COMPLIANT DOCUMENTS (YOU MUST USE THIS EXACT STRUCTURE):
        
        **Executive Summary**
        Site B demonstrates multiple high-severity compliance gaps requiring immediate corrective action. Key violations include overdue LDAR surveys, prohibited high-bleed pneumatic devices, and excessive venting without flare routing.
        
        **Identified Compliance Gaps:**
        
        1. **Gap**: LDAR Survey Frequency Non-Compliance
           **Regulation**: SOR/2018-66, Section 6 - Requires quarterly (3-month) LDAR surveys
           **Severity**: HIGH
           **Rationale**: Last survey completed October 2023 (18 months ago). Facility is 15 months overdue for required quarterly inspections, risking undetected fugitive methane emissions.
        
        2. **Gap**: Prohibited High-Bleed Pneumatic Devices
           **Regulation**: SOR/2018-66, Section 8(1) - Prohibits high-bleed devices (>6 scf/hr) after January 1, 2023
           **Severity**: HIGH
           **Rationale**: 12 high-bleed pneumatic controllers currently in operation (4 separator controls, 6 tank level controls, 2 compressor controls). All must be replaced with low-bleed (<6 scf/hr) or instrument air systems.
        
        3. **Gap**: Excessive Venting Without Flare Routing
           **Regulation**: AER Directive 060, Section 3.2 - Requires flare routing for venting >500 m³/month
           **Severity**: HIGH
           **Rationale**: Facility vents 1,200 m³/month directly to atmosphere (2.4x the threshold). No flare system installed. Immediate flare installation or vapor recovery required.
        
        4. **Gap**: Unauthorized Water Discharge
           **Regulation**: AER Directive 086 - Requires immediate notification of produced water releases
           **Severity**: MEDIUM
           **Rationale**: 15 m³ produced water overflow on Sept 10. Verbal notification only, formal AER notification not submitted within required timeframe.
        
        **Recommended Corrective Actions:**
        1. **Immediate**: Schedule comprehensive LDAR survey within 30 days and establish quarterly survey calendar
        2. **Priority**: Replace all 12 high-bleed pneumatic devices with compliant low-bleed or instrument air systems by Q1 2026
        3. **Critical**: Install flare system or vapor recovery unit to eliminate atmospheric venting, target completion Q2 2026
        
        OUTPUT THE FULL REPORT ABOVE. DO NOT just say "analysis complete".
        """
        
        # Invoke the supervisor workflow
        with st.spinner("Agents working: retriever → gap analyzer → report generator..."):
            state = {"messages": [HumanMessage(content=analysis_prompt)]}
            result_state = agent.invoke(state)
            
           # Extract the final report from messages
            final_report = result_state["messages"][-1].content

        # Display the compliance report
        st.markdown("---")
        st.subheader("📋 Compliance Analysis Report")
        st.markdown(final_report)
        
        # Check if report indicates compliance or gaps
        if any(keyword in final_report.lower() for keyword in ["gap", "deficiency", "non-compliant", "violation", "high", "medium"]):
            st.warning("⚠️ Potential compliance gaps identified. Review recommended actions.")
            # Download button for the report
            st.download_button(
                label="📥 Download Compliance Report",
                data=final_report,
                file_name=f"compliance_report_{uploaded_file.name.replace('.pdf', '')}.txt",
                mime="text/plain"
            )
        else:
            st.success("✅ No significant compliance gaps identified. Operations appear compliant with regulations.")
            st.info("You may continue normal operations. Maintain current monitoring and documentation practices.")
        
    else:
        st.warning("The document does not appear relevant for Oil & Gas compliance. It will not be processed.")
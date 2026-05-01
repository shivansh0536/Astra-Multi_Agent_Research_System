import streamlit as st
import time
from agents import research_graph, chat_chain
import streamlit.components.v1 as components
from fpdf import FPDF
import markdown
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Astra · Agentic OS",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Base Theme ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #f8fafc;
}

.stApp {
    background-color: #03000a;
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(76, 29, 149, 0.25), transparent 25%),
        radial-gradient(circle at 85% 30%, rgba(14, 165, 233, 0.2), transparent 25%);
    background-attachment: fixed;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar (Hidden) ── */
[data-testid="collapsedControl"], [data-testid="stSidebar"] {
    display: none;
}

/* ── Main Area ── */
.main-header {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
}
.main-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(to right, #e2e8f0, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.04em;
    margin-bottom: 0.5rem;
}
.main-subtitle {
    font-size: 1.15rem;
    color: #64748b;
    font-weight: 300;
}

/* ── Inputs & Cards ── */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    color: #f8fafc !important;
    padding: 1rem 1.5rem !important;
    font-size: 1.1rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(56, 189, 248, 0.5) !important;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.15), 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 16px !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    width: 240px !important;
    display: block !important;
    margin: 0 auto !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5) !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
}

/* ── Workflow Steps ── */
.workflow-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 2rem;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 2rem;
    position: relative;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
.workflow-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.8rem;
    flex: 1;
    position: relative;
    z-index: 1;
}
.step-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    color: #64748b;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.step-icon.active {
    background: rgba(56, 189, 248, 0.15);
    border-color: rgba(56, 189, 248, 0.5);
    color: #38bdf8;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.3), inset 0 0 10px rgba(56, 189, 248, 0.2);
}
.step-icon.done {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.5);
    color: #34d399;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
}
.step-label {
    font-size: 0.9rem;
    font-weight: 500;
    color: #94a3b8;
    letter-spacing: 0.02em;
}
.workflow-line {
    position: absolute;
    top: 38%;
    left: 12%;
    right: 12%;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    z-index: 0;
}

/* ── Tabs & Content ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b;
    font-weight: 500;
    padding: 1rem 0;
    font-size: 1.05rem;
}
.stTabs [aria-selected="true"] {
    color: #f8fafc !important;
    border-bottom-color: #8b5cf6 !important;
}
.content-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-top: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
.content-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 1.5rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Top Navigation Bar ───────────────────────────────────────────────────────
col_logo, col_space, col_status = st.columns([2, 5, 2])
with col_logo:
    svg_logo = '''<svg width="28" height="28" viewBox="0 0 24 24" style="margin-right: 10px; margin-bottom: -6px;">
        <defs>
            <linearGradient id="astra-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#8b5cf6" />
                <stop offset="100%" stop-color="#3b82f6" />
            </linearGradient>
        </defs>
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5Z" fill="url(#astra-grad)"/>
    </svg>'''
    st.markdown(f'<div style="font-size: 1.6rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; padding-top: 0.5rem; display: flex; align-items: center;">{svg_logo}Astra <span style="color: #3b82f6; margin-left: 6px;">AI</span></div>', unsafe_allow_html=True)
with col_status:
    st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 1rem; padding-top: 0.8rem;">
            <span style="font-size: 0.85rem; color: #94a3b8;">⚙️ Settings</span>
            <span style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.2);">API Connected</span>
        </div>
    """, unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────────────────
for key in ("results", "running", "done", "topic_input"):
    if key not in st.session_state:
        st.session_state[key] = {} if key == "results" else False if key in ["running", "done"] else ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Main Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">Agentic Intelligence</div>
    <div class="main-subtitle">Deploy a swarm of AI agents to research, synthesize, and draft reports on any topic.</div>
</div>
""", unsafe_allow_html=True)

# ── Input Section ────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    topic = st.text_input(
        "Query", 
        placeholder="Enter your research topic (e.g. Advancements in Solid State Batteries)", 
        label_visibility="collapsed"
    )
    run_btn = st.button("Initialize Swarm")

# ── Logic & Workflow Visualization ───────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        st.session_state.topic_input = topic
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()

r = st.session_state.results
topic_val = st.session_state.topic_input

def get_step_class(step_name):
    if not st.session_state.running and not st.session_state.done:
        return ""
    steps = ["search", "reader", "writer", "critic"]
    if step_name in r:
        return "done"
    if st.session_state.running:
        for k in steps:
            if k not in r:
                return "active" if k == step_name else ""
    return ""

if st.session_state.running or st.session_state.done:
    # Workflow Progress Bar
    st.markdown(f"""
    <div style="position: relative;">
        <div class="workflow-container">
            <div class="workflow-line"></div>
            <div class="workflow-step">
                <div class="step-icon {get_step_class('search')}">🔍</div>
                <div class="step-label">Web Search</div>
            </div>
            <div class="workflow-step">
                <div class="step-icon {get_step_class('reader')}">📄</div>
                <div class="step-label">Data Extraction</div>
            </div>
            <div class="workflow-step">
                <div class="step-icon {get_step_class('writer')}">✍️</div>
                <div class="step-label">Synthesis</div>
            </div>
            <div class="workflow-step">
                <div class="step-icon {get_step_class('critic')}">🧐</div>
                <div class="step-label">Peer Review</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.running and not st.session_state.done:
    status = st.empty()
    status.info("🔍 Search Agent is exploring the web...")
    
    # Stream the LangGraph
    try:
        for event in research_graph.stream({"topic": topic_val, "iterations": 0}):
            for node_name, state_update in event.items():
                if node_name == "search_node":
                    r["search"] = state_update.get("search_data", "")
                    st.session_state.results = r
                    status.info("📄 Reader Agent is extracting content from top sources...")
                elif node_name == "reader_node":
                    r["reader"] = state_update.get("scraped_data", "")
                    st.session_state.results = r
                    status.info("✍️ Writer is drafting the comprehensive report...")
                elif node_name == "writer_node":
                    r["writer"] = state_update.get("draft", "")
                    r["iterations"] = state_update.get("iterations", 1)
                    st.session_state.results = r
                    status.info("🧐 Critic is performing peer review...")
                elif node_name == "critic_node":
                    r["critic"] = state_update.get("critique", "")
                    r["score"] = state_update.get("score", 0)
                    st.session_state.results = r
                    
                    # If the score is less than 8 and we haven't hit the loop limit, it will route back
                    if r["score"] < 8 and r.get("iterations", 1) < 3:
                        st.toast(f"Critic rejected draft (Score: {r['score']}/10). Writer is revising...", icon="🔄")
                        status.warning(f"🔄 Score {r['score']}/10. Writer is revising the draft based on critique...")
                        
                        # Trick the UI into glowing the Writer node again
                        if "critic" in r: del r["critic"]
                        if "writer" in r: del r["writer"]
                        st.session_state.results = r
    except Exception as e:
        status.error(f"⚠️ A connection error occurred: {str(e)}")
        st.session_state.running = False
        st.stop()
    
    status.empty()
    st.session_state.running = False
    st.session_state.done = True
    st.rerun()

# ── Helper for Mermaid ───────────────────────────────────────────────────────
def render_mermaid(text):
    if "```mermaid" not in text:
        st.markdown(text)
        return
        
    parts = text.split("```mermaid")
    st.markdown(parts[0])
    for part in parts[1:]:
        if "```" in part:
            code, rest = part.split("```", 1)
            mermaid_html = f"""
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
            </script>
            <div class="mermaid" style="display: flex; justify-content: center; padding: 20px; color: white;">
                {code}
            </div>
            """
            components.html(mermaid_html, height=500, scrolling=True)
            st.markdown(rest)
        else:
            st.markdown(part)

# ── Helper for PDF Generation ────────────────────────────────────────────────
def generate_pdf(text):
    # Strip Mermaid blocks because FPDF doesn't support them
    text_clean = re.sub(r'```mermaid.*?```', '> *(Note: A visual flowchart is available in the Web UI)*', text, flags=re.DOTALL)
    html_clean = markdown.markdown(text_clean)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    # Write HTML
    pdf.write_html(html_clean)
    # Return as bytes
    return bytes(pdf.output())

# ── Results Presentation ─────────────────────────────────────────────────────
if st.session_state.done and r:
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Final Report", "💬 Chat with Astra", "🧐 Critic Feedback", "🔍 Raw Logs"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        render_mermaid(r["writer"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download buttons in columns
        dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])
        with dl_col1:
            st.download_button(
                label="Download as MD",
                data=r["writer"],
                file_name=f"Astra_Report_{int(time.time())}.md",
                mime="text/markdown",
            )
        with dl_col2:
            try:
                pdf_bytes = generate_pdf(r["writer"])
                st.download_button(
                    label="Download as PDF",
                    data=pdf_bytes,
                    file_name=f"Astra_Report_{int(time.time())}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Could not generate PDF: {e}")
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="content-label">Conversation</div>', unsafe_allow_html=True)
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Chat input
        if prompt := st.chat_input("Ask Astra a follow-up question about the report..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    history_str = "\\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[:-1]])
                    response = chat_chain.invoke({
                        "report": r["writer"],
                        "history": history_str,
                        "question": prompt
                    })
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab3:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(r["critic"])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab4:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="content-label">Search Agent Output</div>', unsafe_allow_html=True)
        st.info(r["search"])
        st.markdown('<br><div class="content-label">Reader Agent Output</div>', unsafe_allow_html=True)
        st.info(r["reader"])
        st.markdown('</div>', unsafe_allow_html=True)
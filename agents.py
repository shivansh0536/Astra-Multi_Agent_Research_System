import re
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from tools import web_search, scrape_url 
from dotenv import load_dotenv

load_dotenv()

# model setup 
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# State
class ResearchState(TypedDict):
    topic: str
    model: str
    search_data: str
    scraped_data: str
    optimist_view: str
    skeptic_view: str
    draft: str
    critique: str
    score: int
    iterations: int

def get_llm(state: ResearchState):
    model_name = state.get("model", "llama-3.3-70b-versatile")
    return ChatGroq(model=model_name, temperature=0)

# 1st agent: Search
def search_node(state: ResearchState):
    topic = state["topic"]
    try:
        search_data = web_search.invoke(topic)
    except Exception as e:
        search_data = f"Error during web search: {str(e)}"
    return {"search_data": search_data}

# 2nd agent: Reader
def reader_node(state: ResearchState):
    topic = state["topic"]
    search_data = state.get("search_data", "")
    llm_dynamic = get_llm(state)
    
    # Ask LLM to pick the top 3 most relevant URLs
    url_selector_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a precise link selector. Read the search results and return the top 3 most relevant URLs to scrape for deeper information on the topic. Return them as a clean, comma-separated list. Do not include any other text, markdown, or explanation. Example: https://example1.com, https://example2.com, https://example3.com"),
        ("human", "Topic: {topic}\n\nSearch Results:\n{search_data}")
    ])
    
    url_chain = url_selector_prompt | llm_dynamic | StrOutputParser()
    try:
        urls_raw = url_chain.invoke({"topic": topic, "search_data": search_data[:2000]})
        urls = [re.sub(r'[`\'"\s]', '', u) for u in urls_raw.split(",") if "http" in u]
    except Exception:
        urls = []
        
    if not urls:
        urls = re.findall(r'https?://[^\s\)\%\}#\]]+', search_data)
        
    scraped_content = ""
    success = False
    
    for url in urls[:3]:
        url = url.strip().strip("[]().,")
        try:
            content = scrape_url.invoke(url)
            if content and not content.startswith("Could not scrape URL"):
                scraped_content = content
                success = True
                break
        except Exception:
            continue
            
    if not success:
        scraped_content = f"Could not scrape detailed content from sources. Falling back to search snippets:\n\n{search_data[:2000]}"
        
    return {"scraped_data": scraped_content}

# 3rd agent: The Optimist
optimist_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the 'Optimist' agent. Your goal is to find the most exciting, high-potential, and positive aspects of the research data. Highlight the breakthroughs, the benefits, and the 'Best Case Scenario'."),
    ("human", "Topic: {topic}\n\nResearch Data:\n{data}\n\nProvide a high-energy, positive perspective on these findings.")
])

def optimist_node(state: ResearchState):
    llm_dynamic = get_llm(state)
    chain = optimist_prompt | llm_dynamic | StrOutputParser()
    data = f"{state.get('search_data', '')}\n\n{state.get('scraped_data', '')}"
    res = chain.invoke({"topic": state["topic"], "data": data[:4000]})
    return {"optimist_view": res}

# 4th agent: The Skeptic
skeptic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the 'Skeptic' agent. Your goal is to identify risks, ethical concerns, technical limitations, and 'Worst Case Scenarios' based on the research data. Be critical but factual."),
    ("human", "Topic: {topic}\n\nResearch Data:\n{data}\n\nProvide a critical, cautious, and skeptical perspective on these findings.")
])

def skeptic_node(state: ResearchState):
    llm_dynamic = get_llm(state)
    chain = skeptic_prompt | llm_dynamic | StrOutputParser()
    data = f"{state.get('search_data', '')}\n\n{state.get('scraped_data', '')}"
    res = chain.invoke({"topic": state["topic"], "data": data[:4000]})
    return {"skeptic_view": res}

# 5th agent: Writer (The Synthesizer)
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research synthesizer. Your job is to weave together research data and two opposing perspectives (Optimist and Skeptic) into a balanced, professional report."),
    ("human", """Write a comprehensive research report on the topic below.

Topic: {topic}

THE OPTIMIST'S VIEW:
{optimist}

THE SKEPTIC'S VIEW:
{skeptic}

Research Data:
{research}

Previous Critique to Address:
{critique}

Structure the report as:
1. Introduction
2. The Clash of Perspectives (Summarize the debate between the Optimist and Skeptic)
3. Key Findings (Minimum 3 points. Wrap any sub-topic that warrants deeper research in double brackets, e.g., [[Specific Tech Name]] or [[Specific Risk Name]])
4. Visual Concept: You MUST include a Mermaid.js flowchart (graph TD). CRITICAL MERMAID RULES: 1) Use single letters for node IDs (A, B, C). 2) All node labels MUST be wrapped in double quotes (e.g., A["Simple Label"]). 3) NEVER use parentheses, brackets, hyphens, colons, or HTML tags inside the labels. 4) Keep it simple (max 6 nodes). Wrap strictly in ```mermaid ... ``` blocks.
5. Conclusion & Future Outlook
6. Sources

Note: The [[Sub-topic]] tags are CRITICAL for the discovery engine. Use them for technical terms or interesting side-topics."""),
])

def writer_node(state: ResearchState):
    llm_dynamic = get_llm(state)
    chain = writer_prompt | llm_dynamic | StrOutputParser()
    research_combined = f"SEARCH RESULTS:\n{state.get('search_data', '')}\n\nDETAILED SCRAPED CONTENT:\n{state.get('scraped_data', '')}"
    critique = state.get("critique", "None")
    
    draft = chain.invoke({
        "topic": state["topic"],
        "research": research_combined[:3000],
        "optimist": state.get("optimist_view", ""),
        "skeptic": state.get("skeptic_view", ""),
        "critique": critique
    })
    
    iters = state.get("iterations", 0) + 1
    return {"draft": draft, "iterations": iters}

# 4th agent: Critic
critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp but fair research critic. Your goal is to ensure the report is high quality, structured correctly, and factual. Do not be overly harsh if the report meets all the basic requirements (Intro, 3 Key Findings, Conclusion, Sources). Give an 8, 9, or 10 if it is genuinely good. Only give below 8 if it is missing a key section or factually poor."),
    ("human", """Review the research report below and evaluate it.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...

Areas to Improve:
- ...

One line verdict:
..."""),
])

def critic_node(state: ResearchState):
    llm_dynamic = get_llm(state)
    chain = critic_prompt | llm_dynamic | StrOutputParser()
    draft = state.get("draft", "")
    critique_text = chain.invoke({"report": draft})
    
    # parse score
    score = 0
    match = re.search(r"Score:\s*(\d+)/10", critique_text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
    else:
        # fallback parsing
        match2 = re.search(r"(\d+)/10", critique_text)
        if match2:
            score = int(match2.group(1))
            
    return {"critique": critique_text, "score": score}

def route_critique(state: ResearchState):
    score = state.get("score", 0)
    iterations = state.get("iterations", 0)
    
    if score >= 8 or iterations >= 3:
        return END
    else:
        return "writer_node"

# Build Graph
workflow = StateGraph(ResearchState)
workflow.add_node("search_node", search_node)
workflow.add_node("reader_node", reader_node)
workflow.add_node("optimist_node", optimist_node)
workflow.add_node("skeptic_node", skeptic_node)
workflow.add_node("writer_node", writer_node)
workflow.add_node("critic_node", critic_node)

workflow.set_entry_point("search_node")
workflow.add_edge("search_node", "reader_node")
workflow.add_edge("reader_node", "optimist_node")
workflow.add_edge("optimist_node", "skeptic_node")
workflow.add_edge("skeptic_node", "writer_node")
workflow.add_edge("writer_node", "critic_node")
workflow.add_conditional_edges("critic_node", route_critique, {
    END: END,
    "writer_node": "writer_node"
})

research_graph = workflow.compile()

# Conversational Follow-up Chain
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Astra AI, an expert research assistant. Answer the user's follow-up questions based on the provided Final Report and conversation history. Be helpful, concise, and highly factual."),
    ("human", """Final Report Context:
{report}

Conversation History:
{history}

User Question: {question}""")
])

def get_chat_chain(model_name: str):
    llm_dynamic = ChatGroq(model=model_name, temperature=0)
    return chat_prompt | llm_dynamic | StrOutputParser()

chat_chain = chat_prompt | llm | StrOutputParser()

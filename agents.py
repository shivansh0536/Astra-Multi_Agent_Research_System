import re
from typing import TypedDict
from langgraph.prebuilt import create_react_agent
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
    search_data: str
    scraped_data: str
    draft: str
    critique: str
    score: int
    iterations: int

# 1st agent: Search
def search_node(state: ResearchState):
    agent = create_react_agent(llm, tools=[web_search])
    topic = state["topic"]
    res = agent.invoke({"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]})
    return {"search_data": res["messages"][-1].content}

# 2nd agent: Reader
def reader_node(state: ResearchState):
    agent = create_react_agent(llm, tools=[scrape_url])
    topic = state["topic"]
    search_data = state.get("search_data", "")
    res = agent.invoke({
        "messages": [("user", f"Based on the following search results about '{topic}', pick the most relevant URL and scrape it for deeper content.\n\nSearch Results:\n{search_data[:1500]}")]
    })
    return {"scraped_data": res["messages"][-1].content}

# 3rd agent: Writer
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Previous Critique to Address (if any):
{critique}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Visual Concept: You MUST include a Mermaid.js flowchart (graph TD). CRITICAL MERMAID RULES: 1) Use single letters for node IDs (A, B, C). 2) All node labels MUST be wrapped in double quotes (e.g., A["Simple Label"]). 3) NEVER use parentheses, brackets, hyphens, colons, or HTML tags inside the labels. 4) Keep it simple (max 6 nodes). Wrap strictly in ```mermaid ... ``` blocks.
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])
writer_chain = writer_prompt | llm | StrOutputParser()

def writer_node(state: ResearchState):
    research_combined = f"SEARCH RESULTS:\n{state.get('search_data', '')}\n\nDETAILED SCRAPED CONTENT:\n{state.get('scraped_data', '')}"
    critique = state.get("critique", "None")
    
    draft = writer_chain.invoke({
        "topic": state["topic"],
        "research": research_combined,
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
critic_chain = critic_prompt | llm | StrOutputParser()

def critic_node(state: ResearchState):
    draft = state.get("draft", "")
    critique_text = critic_chain.invoke({"report": draft})
    
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
workflow.add_node("writer_node", writer_node)
workflow.add_node("critic_node", critic_node)

workflow.set_entry_point("search_node")
workflow.add_edge("search_node", "reader_node")
workflow.add_edge("reader_node", "writer_node")
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
chat_chain = chat_prompt | llm | StrOutputParser()

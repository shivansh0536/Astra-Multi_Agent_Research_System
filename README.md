# Astra AI: Agentic Multi-Agent Research System 🚀

Astra AI is a premium, self-correcting research platform built with **LangGraph**, **Groq (LLaMA 3.3)**, and **Streamlit**. It deploys a swarm of autonomous agents to search, extract, synthesize, and peer-review research reports on any topic.

## Features
- **Cyclic Agentic Loop**: A Critic agent evaluates drafts and forces revisions until a quality threshold (8/10) is met.
- **Conversational Memory**: Chat directly with your research data after the report is generated.
- **Visual Concepts**: Automatically generates Mermaid.js flowcharts for every topic.
- **Multi-Format Export**: Download reports as Markdown or PDF.
- **Premium UI**: Sleek glassmorphism dark mode with real-time workflow visualization.

## Tech Stack
- **Engine**: LangGraph / LangChain
- **LLM**: Groq (LLaMA 3.3 70B)
- **UI**: Streamlit
- **Search**: Tavily

## Setup
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`.
3. Add your `GROQ_API_KEY` and `TAVILY_API_KEY` to a `.env` file.
4. Run: `streamlit run app.py`.

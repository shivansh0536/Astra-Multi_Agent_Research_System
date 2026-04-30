from agents import research_graph, chat_chain
from tools import web_search, scrape_url

def run_research_pipeline(topic: str):
    """Run the full research pipeline for a given topic."""
    print("\n" + "="*50)
    print(f"Starting Astra AI Research Pipeline for: {topic}")
    print("="*50)
    
    final_state = None
    for event in research_graph.stream({"topic": topic, "iterations": 0}):
        for node_name, state_update in event.items():
            if node_name == "search_node":
                print("\n[Step 1] Search Agent: Gathered web data")
            elif node_name == "reader_node":
                print("[Step 2] Reader Agent: Extracted deep content")
            elif node_name == "writer_node":
                print(f"[Step 3] Writer Agent: Draft complete (Iteration {state_update.get('iterations', 1)})")
            elif node_name == "critic_node":
                score = state_update.get("score", 0)
                print(f"[Step 4] Critic Agent: Score {score}/10")
                if score < 8:
                    print("  -> Score below 8. Routing back to Writer for revision...")
            final_state = state_update

    if final_state:
        print("\n" + "="*50)
        print("FINAL REPORT")
        print("="*50)
        # Try to get report from the last state; if not available look for 'draft'
        report = final_state.get("draft", "") or final_state.get("writer", "")
        print(report)

if __name__ == "__main__":
    topic = input("\n Enter a research topic: ")
    run_research_pipeline(topic)

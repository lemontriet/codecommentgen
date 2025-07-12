import os
from langgraph.graph import StateGraph, END
from src.agent_nodes import AgentNodes
from src.utils import load_config
import json

class AgentState(dict):
    code: str
    existing_comment: str
    initial_analysis: dict
    generated_comment: str
    critique_result: dict

if __name__ == "__main__":
    config = load_config()
    agent_nodes = AgentNodes(config)
    workflow = StateGraph(AgentState)
    workflow.add_node("initial_analysis", agent_nodes.initial_analysis_node)
    workflow.add_node("generate_improved_comment", agent_nodes.generate_improved_comment_node)
    workflow.add_node("critique_generated_comment", agent_nodes.critique_generated_comment_node)
    workflow.set_entry_point("initial_analysis")
    workflow.add_edge("initial_analysis", "generate_improved_comment")
    workflow.add_edge("generate_improved_comment", "critique_generated_comment")
    workflow.add_conditional_edges(
        "critique_generated_comment",
        agent_nodes.decide_to_end,
        {
            "retry": "generate_improved_comment",
            "end": END,
        }
    )
    app = workflow.compile()
    examples_path = "data/examples.jsonl"
    examples = []
    if os.path.exists(examples_path):
        with open(examples_path, 'r', encoding='utf-8') as f:
            examples = [json.loads(line) for line in f]

    while True:
        mode = input("Choose mode: (1) Interactive, (2) Run Examples, (quit) Exit: ").lower()
        if mode == 'quit':
            break
        elif mode == '1':
            user_code = input("Enter Python code:\n")
            user_comment = input("Enter existing comment (leave blank if none):\n")
            if not user_code.strip():
                continue
            initial_state = {
                "code": user_code,
                "existing_comment": user_comment if user_comment.strip() else "No comment provided."
            }
            final_state = app.invoke(initial_state)
            if final_state:
                print(f"Original Code:\n{initial_state['code']}")
                print(f"Original Comment: {initial_state['existing_comment']}")
                # Initial analysis
                initial_analysis = final_state.get('initial_analysis', {})
                print(f"Initial Analysis Rating (Original Comment): {initial_analysis.get('quality_rating', 'N/A')}/5")
                print(f"Initial Analysis Assessment: {initial_analysis.get('assessment', 'N/A')}")
                print(f"Initial Analysis Suggestions: {initial_analysis.get('suggestions', 'N/A')}")
                # Agentic comments
                print(f"Generated Comment: {final_state.get('generated_comment', 'N/A').strip()}")
                if 'critique_result' in final_state:
                    print(f"Critique Rating: {final_state['critique_result'].get('rating', 'N/A')}")
                    print(f"Critique Feedback: {final_state['critique_result'].get('feedback', 'N/A')}")
        elif mode == '2':
            if not examples:
                print("No examples to run.")
                continue
            for i, example in enumerate(examples):
                initial_state = {
                    "code": example["code"],
                    "existing_comment": example.get("comment", "No comment provided.")
                }
                final_state = app.invoke(initial_state)
                if final_state:
                    print(f"Code:\n{example['code'][:100].strip()}...")
                    print(f"Original Comment: {initial_state['existing_comment'].strip()}")
                    # Initial analysis
                    initial_analysis = final_state.get('initial_analysis', {})
                    print(f"Initial Analysis Rating (Original Comment): {initial_analysis.get('quality_rating', 'N/A')}/5")
                    print(f"Initial Analysis Assessment: {initial_analysis.get('assessment', 'N/A')}")
                    print(f"Initial Analysis Suggestions: {initial_analysis.get('suggestions', 'N/A')}")
                    # Agent's comments
                    print(f"Generated Comment: {final_state.get('generated_comment', 'N/A').strip()}")
                    if 'critique_result' in final_state:
                        print(f"Critique Rating: {final_state['critique_result'].get('rating', 'N/A')}")
                        print(f"Critique Feedback: {final_state['critique_result'].get('feedback', 'N/A').strip()}")
                    print("-" * 30)
        else:
            print("Invalid mode.")
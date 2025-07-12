import json
from src.utils import get_llm, get_prompt, get_json_parser
from langchain_core.exceptions import OutputParserException

class AgentNodes:
    def __init__(self, config):
        self.config = config
        self.llm = get_llm(config)
        self.json_parser = get_json_parser()

    def initial_analysis_node(self, state):
        code = state.get("code", "")
        existing_comment = state.get("existing_comment", "No comment provided.")
        prompt = get_prompt("initial_analysis", self.config).format(
            code=code,
            existing_comment=existing_comment
        )
        response_content = self.llm.invoke(prompt)
        try:
            analysis_result = self.json_parser.parse(response_content)
        except OutputParserException as e:
            analysis_result = {
                "quality_rating": 1,
                "assessment": "Failed to parse initial analysis. Assuming poor quality.",
                "suggestions": ["Ensure the comment is clear, complete, and accurate, and follows a standard format."],
                "existing_comment_good": False
            }
        state["initial_analysis"] = analysis_result
        return state

    def generate_improved_comment_node(self, state):
        code = state["code"]
        suggestions = state["initial_analysis"]["suggestions"]
        prompt = get_prompt("generate_improved_comment", self.config).format(
            code=code,
            suggestions="\n".join([f"- {s}" for s in suggestions])
        )
        new_comment = self.llm.invoke(prompt).strip()
        state["generated_comment"] = new_comment
        return state

    def critique_generated_comment_node(self, state):
        code = state["code"]
        original_comment = state.get("existing_comment", "No comment provided.")
        generated_comment = state["generated_comment"]
        prompt = get_prompt("critique_generated_comment", self.config).format(
            code=code,
            original_comment=original_comment,
            generated_comment=generated_comment
        )
        response_content = self.llm.invoke(prompt)
        try:
            critique_result = self.json_parser.parse(response_content)
        except OutputParserException as e:
            critique_result = {
                "rating": 1,
                "feedback": "Failed to parse critique. Ensure JSON format.",
                "ready_for_output": False
            }
        state["critique_result"] = critique_result
        return state

    def decide_to_end(self, state):
        # End if initial input/generated output is good enough
        if state.get("critique_result", {}).get("ready_for_output", False):
            print("Critique: Ready for output. Ending workflow.")
            return "end"
        elif state.get("initial_analysis", {}).get("existing_comment_good", False):
            print("Initial analysis: Existing comment is good. Ending workflow.")
            return "end"
        else:
            # Loop until comment is good enough
            print("Critique: Not ready for output. Retrying comment generation.")
            return "retry"
import yaml
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def load_config(config_path="configs/agent_config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    
def agent_config_to_llm(config):
    llm_config = config['llm']
    return Ollama(
        model = llm_config['model_name'],
        base_url = llm_config['base_url'],
        temperature = llm_config['temperature'],
        num_predict = llm_config['max_tokens']
    )

def get_prompt(template_name, config):
    template_str= config['prompts'][template_name]
    return PromptTemplate.from_template(template_str)

def get_json_parser():
    return JsonOutputParser
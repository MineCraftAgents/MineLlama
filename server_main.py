import argparse
import json
from minellama import Minellama
import config
import os
import time

# Load API keys from config
openai_api_key = config.OPEN_AI_API_KEY
hf_auth_token = config.HUGGING_FACE_AUTH_KEY

screen_name = "screen_name"
mc_port_number = "99999"
server_port_num = "enter your port number"

# Set up argument parser
parser = argparse.ArgumentParser(description="Run Minellama experiments.")

parser.add_argument("--llm", type=str, default="gpt", choices=["gpt", "llama"],
                    help="Choose the LLM backend: 'gpt' for OpenAI or 'llama' for LLaMA2")
parser.add_argument("--llm_model", type=str, default="gpt-3.5-turbo",
                    help="Model name: 'gpt-3.5-turbo', 'gpt-4', or LLaMA2 model like 'meta-llama/Llama-2-70b-chat-hf'")
parser.add_argument("--rag_switch", type=str, default="True", choices=["True", "False"],
                    help="Enable or disable RAG retrieval (True/False)")
parser.add_argument("--search_switch", type=str, default="True", choices=["True", "False"],
                    help="Enable or disable prior search of item information(recipe agent) (True/False)")
parser.add_argument("--use_fixed_data", type=str, default="True", choices=["True", "False"],
                    help="Use fixed data for the experiment (True/False)")
# parser.add_argument("--experiment_number_total", type=int, default=5,
#                     help="Total number of experiments to run")

# #* タスクを外部から渡す
parser.add_argument("--task_item", type=str)
args = parser.parse_args()

# Convert rag_switch from string to boolean
args.rag_switch = args.rag_switch.lower() == "true"
args.search_switch = args.search_switch.lower() == "true"
args.use_fixed_data = args.use_fixed_data.lower() == "true"


minellama = Minellama(
    openai_api_key=openai_api_key,
    hf_auth_token=hf_auth_token,
    mc_port=mc_port_number,
    server_port=server_port_num,
    llm=args.llm,
    llm_model=args.llm_model,
    local_llm_path = None, # If you have local Llama2, set the path to the directory. If None, it will create the model dir in minellama/llm/ .
    difficulty= "peaceful",
    record_file= "./log.txt", # the ouput file 
    rag_switch=args.rag_switch,
    search_switch=args.search_switch,
    use_fixed_data = args.use_fixed_data
)


task_list = [{args.task_item: 1}]

#! botに権限付与
os.system(f'screen -S {screen_name} -X stuff "op bot\n"')
minellama.inference(task=task_list)

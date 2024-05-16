from minellama import Minellama

openai_api_key = "OPEN_AI_API_KEY"
hf_auth_token = "HUGGING_FACE_AUTH_KEY"

minellama = Minellama(
    openai_api_key=openai_api_key,
    hf_auth_token=hf_auth_token,
    mc_port="MINECRAFT_PORT_KEY",
    llm = "llama", #"llama" or "gpt"
    llm_model = "meta-llama/Llama-2-70b-chat-hf", #"meta-llama/Llama-2-70b-chat-hf" or "meta-llama/Llama-2-7b-chat-hf" for Llama2, "gpt-3.5-turbo" or "gpt-4" for GPT
    local_llm_path = None, # If you have local Llama2, set the path to the directory. If None, it will create the model dir in minellama/llm/ .
    difficulty= "peaceful",
    record_file= "./log.txt" # the ouput file 
)


task = [{"stick":1},{"crafting_table":1},{"wooden_pickaxe":1},{"stone_pickaxe":1}, {"iron_pickaxe":1},{"cooked_beef":1}, {"white_bed":1}]
minellama.inference(task=task)
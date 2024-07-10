from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from llama_index.prompts.prompts import SimpleInputPrompt,PromptTemplate
from llama_index.llms import HuggingFaceLLM
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import set_global_service_context
from llama_index import ServiceContext
from llama_index import VectorStoreIndex, download_loader, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.schema import TextNode
from pathlib import Path
import re
import json
import os



class Llama2:
    def __init__(self,hf_auth_token, llm_model="meta-llama/Llama-2-70b-chat-hf", local_llm_path=None):
        self.auth_token = hf_auth_token
        self.name = llm_model
        if local_llm_path:
            cache_dir = Path(local_llm_path)
        else:
            cache_dir = Path(__file__).parent / "model"
        self.tokenizer = AutoTokenizer.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token)
        self.model = AutoModelForCausalLM.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token, torch_dtype=torch.float16, 
            rope_scaling={"type": "dynamic", "factor": 2}, load_in_8bit=True, device_map='auto') 

    ###with RAG
    def content(self, system_prompt="",  query_str="", index_dir="", data_dir="", persist_index=True, similarity_top_k = 2, context_window=4096, max_new_tokens=1024):#persist_index=True, similarity_top_k = 1 から変更している。
        data_path = "minellama/llm/data/modified_minecraft_data/"
        index_dir = "minellama/llm/data/chached_data/"

        print("\n================Called LLM with RAG====================")
        query_wrapper_prompt = PromptTemplate("[INST]<<SYS>>\n" + system_prompt + "<</SYS>>\n\n{query_str}[/INST]")

        llm = HuggingFaceLLM(context_window=context_window,
                            # max_new_tokens=256,
                            max_new_tokens=max_new_tokens,
                            # system_prompt=system_prompt,
                            query_wrapper_prompt=query_wrapper_prompt,
                            model=self.model,
                            device_map="auto",
                            tokenizer=self.tokenizer)
 
        embeddings=LangchainEmbedding(
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )

        service_context = ServiceContext.from_defaults(
            chunk_size=1024,
            llm=llm,
            embed_model=embeddings
        )
        set_global_service_context(service_context)

        # ragのファイルの読み込みを指定したディレクトリ内すべてのファイルにする場合。
        # -------------------------------------------------------------------------------------------
        file_list = os.listdir(f"{str(data_path)}")
        if persist_index:
            if not os.path.isdir(index_dir):
                print("No vector index found. Making new one...")
                nodes=[]
                idnum = 1
                for ref_filename in file_list:
                    ref_path = f"{str(data_path)}{ref_filename}"
                    with open(ref_path, 'r', encoding='utf-8') as file:
                        for line_number, text in enumerate(file, start=idnum):
                            node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                            idnum = idnum + 1
                            if node.text:
                                nodes.append(node)
                index = VectorStoreIndex(nodes)
                index.storage_context.persist(persist_dir=index_dir)
                print("Vector index stored.")
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(storage_context)

        else:
            print("Without Vector DB.")
            nodes=[]
            for ref_filename in file_list:
                ref_path = f"{str(data_path)}/{ref_filename}"
                with open(ref_path, 'r', encoding='utf-8') as file:
                    for line_number, text in enumerate(file, start=1):
                        node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                        if node.text:
                            nodes.append(node)
            index = VectorStoreIndex(nodes)
        #-------------------------------------------------------------------------------------------
        
        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(query_str)
        print(response.get_formatted_sources())
        print(response)
        return str(response)
    

#===========recipe===================
    def extract_dict_from_str(self,response:str)->dict:
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            # print("json_dict: ",json_dict)
            return json.loads(json_dict)
        else:
            print("No json dict found. Trying again.")
            raise Exception("Invalid Format Error")

        
    def check_keys_of_response(self,response:dict) -> None:
        if not (set(response.keys()) == set(["name", "count", "requirements"])):
            raise KeyError

    def query_wrapper(self, query_item:str)->dict[int]:
        prompt = f'To make some "{query_item}", you need'
        system_prompt = """
Please list the items and their quantities needed to craft items.
Use the json-like format provided in the examples below for your answers.
Please note that there are no "logs", it must be "log".

Example 1: 
To make 1 "netherite_boots", you need 1 "diamond_boots" and 1 "netherite_ingot". Then, Answer like
{{"name": "netherite_boots", "count": 1, "requirements": {{"diamond_boots": 1, "netherite_ingot": 1}}}}

Example 2: 
To make 1 "stone_block_slab3", you need 1 "stone".
{{"name": "stone_block_slab3", "count": 1, "requirements": {{"stone": 1}}}}

Example 3:
To make 1 "wheat_stone", you need no materials. Then, Answer like
{{"name": "wheat_stone", "count": 1, "requirements": "None"}}

Example 4:
To make 1 "egg_plant", you need no materials. Then, Answer like
{{"name": "egg_plant", "count": 1, "requirements": "None"}}

Note that when you need no materials to get the item, you must answer "None" for "requirements".
Remember to focus on the format as demonstrated in the examples. 
"""
        # print(prompt)
        max_request = 10
        while max_request > 0:
            try:
                response = self.content(system_prompt=system_prompt, query_str=prompt)#, index_dir="recipes_dataset"
                # print(response)
                # print("\n")
                response = self.extract_dict_from_str(response)
                print("Extracted Dict: ", response)
                self.check_keys_of_response(response)
                break
            except Exception as e:
                print(e)
                max_request -= 1
                continue
        return response


    def resolve_dependency_all(self,init_list:list[str]):
        def resolve_dependency_from_list(query_item_list:list[str])-> list[dict]:
            return [ self.query_wrapper(item) for item in query_item_list]
        dependency_list:list[dict] = []
        resolved_edge:list[str] = []
        unresolved_edge:list[str] = init_list
        resolve_count = 10

        while len(unresolved_edge) and (resolve_count > 0):
            print(resolved_edge)
            print(unresolved_edge)
            dependency_list += resolve_dependency_from_list(unresolved_edge)
            resolved_edge += unresolved_edge
            unresolved_edge = []
            for dep in dependency_list:
                print("Dependency: ",dep)
                if isinstance(dep["requirements"],dict):
                    for value in dep["requirements"].keys():
                        if (value not in resolved_edge) and (value != ""):
                            unresolved_edge.append(value)
            
            resolve_count -= 1
            unresolved_edge = list(set(unresolved_edge))
        return dependency_list

    def create_recipe_dict(self, dependency_list):
        recipe_dict = {}
        for item in dependency_list:
            if item["requirements"] == "None":
                item["requirements"] = None
            recipe_dict[item["name"]] = item["requirements"]
        return recipe_dict

    def get_recipe(self, query_item_list): 
        dependency_list = self.resolve_dependency_all(query_item_list)
        recipe_dict = self.create_recipe_dict(dependency_list=dependency_list)

        return recipe_dict
    

#=======generate action=======
    def extract_jscode(self, response = ""):
        js_code_match = re.search(r'(await.*?;)', response, re.DOTALL)
        if js_code_match:
            js_code = js_code_match.group(1).strip()
            print("============= Code Extraction Success ============= \n",js_code)
            return js_code
        else:
            print("No JavaScript code found after 'YOUR ANSWER'. Trying again.")
            return None
    

    def generate_action(self, task="", context="", error_message="", index_dir="context", max_iterations=10):
        iterations = 0
        system_prompt = '''
You are a helpful assistant of Minecraft game.
I want you to choose one function to achive the task.

Here are some javascript function:
1) craft(bot, item, count); //Use this to craft item. 
2) smelt(bot, item, count, fuel); //Use this to smelt item. fuel should be 'planks'.
3) mine(bot, item, count, tool); //Use this to mine item. When you need tools to mine, give it as an argument, e.g. 'wooden_pickaxe' to mine stone.
4) kill(bot, entity, count, tool); //Use this to get item by killing entities. When you need tools to kill, give it as an argument, e.g. 'wooden_sword'.

I will give you the following information for each time:
Task: {{"name":count}}

Please note that
1) The arguments item should be string and count should be number, and the first argument must be bot.
2) You have to call only one function with 'await', e.g. await craft(bot, 'stone_pickaxe',1);
3) Please use underscores _ instead of spaces for the names and tools, e.g. not 'crafting table' but 'crafting_table'
4) Be careful with the argument 'count', put the correct number in it. Please pay attention to Task dict, which indicates 'count' as the argument.
5) Context might be wrong. Don't rely too much on it. Don't put the ingredients as the argument. You don't need to care the ingredients. Follow the format above and put the arguments carefully. 

Here are some examples:
Example 1)
Task: {{"cobblestone":3}}
Context: You need wooden_pickaxe to mine cobblestone.
Then, you would answer:
await mine(bot, 'cobblestone', 3, 'wooden_pickaxe');

Example 2)
Task: {{"beef":2}}
Context: You have to kill a cow to get beef.
Then, you would answer:
await kill(bot, 'cow', 2);

Example 3)
Task: {{"iron_sword":1}}
Context: You have to craft it with crafting table.
Then, you would answer:
await craft(bot, 'iron_sword',1);

Example 4)
Task: {{"iron_ingot":2}}
Context: You have to smelt raw_iron to get iron_ingot.
Then, you would answer:
await smelt(bot, 'raw_iron', 2, 'planks');


'''
        human_prompt = f'''
Choose the function with the arguments to achive the task below please.
Task : {task}
'''

        while iterations < max_iterations:
            output = self.content(system_prompt=system_prompt,query_str=human_prompt, index_dir=index_dir)
            print(output)
            code = self.extract_jscode(response = output)
            if code is not None:
                return code
            iterations += 1
            print("Current iterations: ", iterations)

        print("You reached tha max iterations.")
        return 

    


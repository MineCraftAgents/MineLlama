from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from llama_index.prompts.prompts import SimpleInputPrompt
from llama_index.llms import HuggingFaceLLM
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import set_global_service_context
from llama_index import ServiceContext
from llama_index.node_parser.text import SentenceSplitter
from llama_index import VectorStoreIndex, download_loader, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.schema import TextNode
from pathlib import Path
import re
import json
import os
import time


class GPT:
    def __init__(self, llm_model="gpt-3.5-turbo", embed_model="text-embedding-3-small"):
        self.llm_model = llm_model
        self.embed_model = embed_model


    def create_index_with_directory(self, directory_name, index_dir, context_window=8192, max_new_tokens=1024):
        data_path = "data/minecraft_data/"+ directory_name
        data_path = Path(__file__).parent / data_path
        index_dir = "data/db/"+index_dir
        index_dir = Path(__file__).parent / index_dir

        print("\n================Called LLM with RAG====================")

        service_context = ServiceContext.from_defaults(
            llm=OpenAI(model=self.llm_model),
            embed_model=OpenAIEmbedding(model=self.embed_model,dimensions=384),
            node_parser=SentenceSplitter(chunk_size=512, chunk_overlap=20),
            num_output=512,
            context_window=3900,
        )
        # And set the service context
        set_global_service_context(service_context)

        nodes=[]
        file_path = str(data_path) + f"/{directory_name}.txt"
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, text in enumerate(file, start=1):
                node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                nodes.append(node)
        index = VectorStoreIndex(nodes)
        index.storage_context.persist(persist_dir=index_dir)
        print("Vector index stored.")



    def content(self, system_prompt="", human_prompt="", query_str="", index_dir=None, context_window=8192, max_new_tokens=1024, max_retries = 3, retry_delay=30):
        index_dir = "data/db/"+index_dir
        index_dir = Path(__file__).parent / index_dir

        print("\n================Called LLM with RAG====================")
        query_wrapper_prompt = SimpleInputPrompt("{query_str} [/INST]")
        query_wrapper_prompt.format(query_str=query_str)

        # Create new service context instance
        service_context = ServiceContext.from_defaults(
            llm=OpenAI(model=self.llm_model),
            embed_model=OpenAIEmbedding(model=self.embed_model,dimensions=384),
            node_parser=SentenceSplitter(chunk_size=512, chunk_overlap=20),
            system_prompt=system_prompt,
            num_output=512,
            context_window=3900,
        )
        # And set the service context
        set_global_service_context(service_context)

        # Create an index - we'll be able to query this in a sec
        # index = VectorStoreIndex.from_documents(documents)
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        index = load_index_from_storage(storage_context)

        # Setup index query engine using LLM 
        query_engine = index.as_query_engine()

        # # Test out a query in natural
        # response = query_engine.query("In the case of nonlinear utility functions, what were the results of optimality rate for HC and AR respectively, for the 10 issue case?")
        for attempt in range(max_retries):
            try:
                response = query_engine.query(human_prompt)
                print("Source:")
                print(response.get_formatted_sources())
                # print(response)
                return str(response)
            except Exception as e:
                print(f"Error occured: {e}")
                if attempt < max_retries - 1:
                    print(f"Retry {retry_delay} sec later...")
                    time.sleep(retry_delay)
                else:
                    print("Reached max_retries.")
                    raise
                
    

#===========recipe===================
    def extract_dict_from_str(self,response:str)->dict:
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            print("json_dict: ",json_dict)
            return json.loads(json_dict)
        else:
            print("No json dict found. Trying again.")
            raise Exception("Invalid Format Error")

        
    def check_keys_of_response(self,response:dict) -> None:
        if not (set(response.keys()) == set(["name", "count", "requirements"])):
            raise KeyError

    def query_wrapper(self, query_item:str)->dict[int]:
        prompt = f'Please give me the python dict to make some "{query_item}".'
        system_prompt = """
Please list the items and their quantities needed to craft items.
Use the python dict format provided in the examples below for your answers.
Please note that there are no "logs", it must be "log".

Format:
{"name":..., "count":..., "requirements":...}

Example 1: 
To make 1 "netherite_boots", you need 1 "diamond_boots" and 1 "netherite_ingot". Then, Answer like
{"name": "netherite_boots", "count": 1, "requirements": {"diamond_boots": 1, "netherite_ingot": 1}}

Example 2: 
To make 1 "stone_block_slab3", you need 1 "stone".
{"name": "stone_block_slab3", "count": 1, "requirements": {"stone": 1}}

Example 3:
To make 1 "wheat_stone", you need no materials. Then, Answer like
{"name": "wheat_stone", "count": 1, "requirements": "None"}

Example 4:
To make 1 "egg_plant", you need no materials. Then, Answer like
{"name": "egg_plant", "count": 1, "requirements": "None"}

Note that when you need no materials to get the item, you must answer "None" for "requirements".
Remember to focus on the format as demonstrated in the examples. 
"""
        # print(prompt)
        max_request = 10
        while max_request > 0:
            try:
                response = str(self.content(system_prompt=system_prompt, human_prompt=prompt, index_dir="recipes_dataset-gpt"))
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

    def get_recipe(self, query_item_list, reset_db=False):
        # Reset vector index, or create it if no index found.
        # if reset_db:
        #     self.create_index_with_directory(directory_name="recipes_dataset", index_dir="recipes_dataset")
        index_dir = "data/db/recipes_dataset-gpt"
        index_dir = Path(__file__).parent / index_dir
        if not os.path.isdir(index_dir):
            print("No vector index found. Making new one...")
            self.create_index_with_directory(directory_name="recipes_dataset", index_dir="recipes_dataset-gpt")
            
        dependency_list = self.resolve_dependency_all(query_item_list)
        recipe_dict = self.create_recipe_dict(dependency_list=dependency_list)

        return recipe_dict
    
#=========context============
    def extract_context(self, response):
        json_match = re.search(r'({.*?"action":.*?})', response, re.DOTALL)
        if json_match:
            json_dict = json_match.group(1).strip()
            print("json_dict: ",json_dict)
            if "action" in json_dict and "tool" in json_dict:
                print("============= Context Extraction Success ============= ")
                return json_dict
            else:
                print("Could't find required keys in the dict.")
        else:
            print("No json dict found. Trying again.")
        return None
        

        

    def get_context(self, task, inventory="", reset_db=False,  max_iterations=10):
        # Reset vector index, or create it if no index found.
        if reset_db:
            self.create_index_with_directory(directory_name="context", index_dir="context-gpt")
        index_dir = "data/db/context-gpt"
        index_dir = Path(__file__).parent / index_dir
        if not os.path.isdir(index_dir):
            print("No vector index found. Making new one...")
            self.create_index_with_directory(directory_name="context", index_dir="context-gpt")
        
        system_prompt = '''
You are a helpful assistant of Minecraft game.
I want you to suggest how to obtain the item.
Each time I will give you the following information:
Task: ...

I want you to suggest which actions to take (e.g. mine, kill, craft, or smelt), targets,  and the required tools if need (e.g. stone_pickaxe to mine raw_iron).
You can choose the action to obtain the item from 4 choices: mine, kill, craft, or smelt.
Required tool is a tool to get the item, e.g. stone_pickaxe, furnace, crafting_table, etc. Don't mention ingredients or recipes.
If you don't need any tool, answer "None".
Target is a target of the action.
You must answer with the json format as below:
{"action":"...", "target":"...", "tool":"..."}

Example 1)
Task: {"diamond_ore":4}
Then, you would answer:
{"action":"mine", "target":"diamond_ore", "tool":"iron_pickaxe"}

Example 2)
Task: {"golden_pickaxe":2}
Then, you would answer:
{"action":"craft", "target":"golden_pickaxe", "tool":"crafting_table"}

Example 3)
Task: {"iron_ingot":3}
Then, you would answer:
{"action":"smelt", "target":"raw_iron", "tool":"furnace"}

Example 4)
Task: {"beef":1}
Then, you would answer:
{"action":"kill", "target":"cow", "tool":"None"}
'''
        human_prompt = f'''
What are the right action and the required tool with the json format to obtain the item in the task below?
Task: {task}
'''
        iterations = 0
        while iterations < max_iterations:
            print("Current iterations: ", iterations)
            output = self.content(system_prompt=system_prompt, human_prompt=human_prompt, index_dir="context-gpt")
            # print(output)
            context = self.extract_context(output)
            if context is not None:
                print("======== Context from LLM ========\n", context)
                return context
            iterations += 1
        print("Max iterations reached.")
        # output = self.content(system_prompt=system_prompt, human_prompt=human_prompt, index_dir="context")
        
        return None
    
#=======generate action=======
    def extract_jscode(self, response = ""):
        js_code_match = re.search(r'(await.*?;)', response, re.DOTALL)
        if js_code_match:
            js_code = js_code_match.group(1).strip()
            print("============= Code Extraction Success ============= \n",js_code)
            return js_code
        else:
            print("No JavaScript code found. Trying again.")
            return None
    


    def generate_action_with_rag(self, task="", context="", error_message="", reset_db=False, max_iterations=10):
        # Reset vector index, or create it if no index found.
        if reset_db:
            self.create_index_with_directory(directory_name="action", index_dir="action")
        index_dir = "data/db/context-gpt"
        index_dir = Path(__file__).parent / index_dir
        if not os.path.isdir(index_dir):
            print("No vector index found. Making new one...")
            self.create_index_with_directory(directory_name="context", index_dir="context-gpt")
            
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
Task: {'name':count}

Follow the format of your response below:
await FUNCTION(ARGUMENT);

Please note that
1) The arguments item should be string and count should be number, and the first argument must be bot.
2) You have to call only one function with 'await', e.g. await craft(bot, 'stone_pickaxe',1);
3) Please use underscores _ instead of spaces for the names and tools, e.g. not 'crafting table' but 'crafting_table'
4) Be careful with the argument 'count', put the correct number in it. Please pay attention to Task dict, which indicates 'count' as the argument.
5) Context might be wrong. Don't rely too much on it. Don't put the ingredients as the argument. You don't need to care the ingredients. Follow the format above and put the arguments carefully. 

Here are some examples:
Example 1)
Task: {"cobblestone":3}
Context: You need wooden_pickaxe to mine cobblestone.
Then, you would answer:
await mine(bot, 'cobblestone', 3, 'wooden_pickaxe');

Example 2)
Task: {"beef":2}
Context: You have to kill a cow to get beef.
Then, you would answer:
await kill(bot, 'cow', 2);

Example 3)
Task: {"iron_sword":1}
Context: You can craft iron_sword with crafting table.
Then, you would answer:
await craft(bot, 'iron_sword',1);

Example 4)
Task: {"iron_ingot":2}
Context: You have to smelt raw_iron to get iron_ingot.
Then, you would answer:
await smelt(bot, 'raw_iron', 2, 'planks');

'''
        human_prompt = f'''
Choose the function with the arguments to achive the task below please.
Task : {task}
'''

        while iterations < max_iterations:
            print("Current iterations: ", iterations)
            output = self.content(system_prompt=system_prompt,human_prompt=human_prompt, index_dir="context-gpt")
            # Extract javascript action code from the response.
            code = self.extract_jscode(response = output)
            if code is not None:
                return code
            print(output)
            iterations += 1

        print("You reached tha max iterations.")
        return 

    



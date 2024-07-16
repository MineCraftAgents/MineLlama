import re
import json

class RecipeGenerator:
    def __init__(self, llm):
        self.llm = llm

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
                response = self.llm.content(system_prompt=system_prompt, query_str=prompt, index_dir="recipes_dataset")
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
    
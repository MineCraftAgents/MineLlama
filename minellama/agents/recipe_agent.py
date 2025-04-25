import json 
from pathlib import Path
import random
import math
import re
import copy
import sys
from rich import print
from rich.tree import Tree
import time

import sys
import os
sys.setrecursionlimit(3000)  # 再帰の深さの制限を2000に設定


class RecipeAgent:
    def __init__(self,llm=None, search_switch=False):
        self.data_path = str(Path(__file__).parent / "minecraft_dataset")
        with open(f"{self.data_path}/recipes_bedrock.json", "r") as f:
            self.recipe_data = json.load(f)
        with open(f"{self.data_path}/recipes_success.json", "r") as f:
            self.recipe_data_success = json.load(f)
        with open(f"{self.data_path}/blocks_bedrock.json", "r") as f:
            self.blocks_data = json.load(f)
        with open(f"{self.data_path}/dropitems_bedrock.json", "r") as f:
            self.entity_items_data = json.load(f)
        with open(f"{self.data_path}/harvest_tools.json", "r") as f:
            self.harvest_tools = json.load(f)
        with open(f"{self.data_path}/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}

        #biome: 後にレシピルートの選択でLLMを用いる可能性がある。
        self.llm = llm
        #* RAGを使わずにアイテムを処理するために検索を行っている場合に、LLMにそれを示す変数
        self.search_switch = search_switch
        
        self.inventory={}
        self.initial_inventory = {}
        self.biome = ""
        self.nearby_block = []
        self.nearby_entities = []
        self.equipment = []
        self.chat_log = ""
        self.error = ""

        self.recipe_dependency_list = {}
        self.searched_list = []
        self.paths = []
        self.goal_items = []
        self.current_goal_memory = []

        self.recipe_memory_success = {}
        self.recipe_memory_failed = {}

        # crafting_talbeなしで作れるアイテム
        self.items_without_crafting_table = ["crafting_table", "planks", "stick"]

        self.use_recipe_data_success = True

        self.iterations = 0
        # ✅ Add this line to initialize difficulty tracking
        self.item_difficulty = {}  # {"stick": 5, "planks": 2, ...}

    # ✅ Add this method to RecipeAgent
    def adjust_difficulty(self, item: str, success: bool):
        if item not in self.item_difficulty:
            self.item_difficulty[item] = 5  # default medium difficulty

        if success:
            self.item_difficulty[item] = max(1, self.item_difficulty[item] - 1)
        else:
            self.item_difficulty[item] = min(100, self.item_difficulty[item] + 1)

        print(f"📊 Difficulty of '{item}' is now {self.item_difficulty[item]}")

    # item名がMinecraftに存在するかどうか判定
    def check_item_name(self, name:str):
        if name in self.mc_items:
            return
        else:
            # error = f"There is no item called {name} in Minecraft game."
            error = f"Use correct item name registered in Minecraft Game."
            raise Exception(error)
        
    def complete_checker(self, goal:dict):
        for key in list(goal.keys()):
            diff = self.get_inventory_diff(goal, key)
            if diff == 0:
                done = True
            else:
                done = False
                return done
        return done
    
    def reset(self):
        self.inventory={}
        self.initial_inventory = {}
        self.biome = ""
        self.nearby_block = []
        self.nearby_entities = []
        self.equipment = []
        self.chat_log = ""
        self.error = ""
        self.recipe_dependency_list = {}
        self.searched_list = []
        self.paths = []
        self.goal_items = []
        self.current_goal_memory = []
        self.recipe_memory_success = {}
        self.recipe_memory_failed = {}
    
    def update_info(self, inventory=None, biome=None, nearby_block=None, nearby_entities=None, equipment=None, chat_log=None, error=None):
        if inventory is not None:
            self.inventory = inventory

        if biome is not None: 
            self.biome = biome

        if nearby_block is not None:
            self.nearby_block = nearby_block

        if nearby_entities is not None:
            self.nearby_entities = nearby_entities
        
        if equipment is not None:
            self.equipment = equipment

        if chat_log is not None:
            self.chat_log = chat_log
        
        if error is not None:
            self.error = error

    def update_initial_inventory(self, inventory:dict):
        self.initial_inventory = inventory


    # ========= recipe dependencies ========     
    def extract_dict_from_str(self,response:str)->dict:
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            return json.loads(json_dict.replace("'", '"'))
        else:
            raise Exception("No python dict found. Trying again.")#"Please output python-dict data."
        
    def check_keys_of_response(self,response:dict) -> None:
        if not (set(response.keys()) == set(["name", "count", "required_items", "action"])):
            raise KeyError
        
    def check_infinit_loop(self, key):
        if key in self.recipe_dependency_list:
            if self.recipe_dependency_list[key]["required_items"] and key in self.recipe_dependency_list[key]["required_items"]:
                raise Exception(f"There is an infinit loop in recipe list. Please avoid {key}.")
    
    def item_name_validation(self, response:dict) -> None:
        name = response["name"]
        self.check_item_name(name)
        required_items = response["required_items"]
        if isinstance(required_items, dict):
            for key in required_items:
                self.check_item_name(key)
                self.check_infinit_loop(key)

    def inventory_to_sentence(self):
        items = [f"{value} {key}" for key, value in self.inventory.items()]
        if len(items) > 1:
            return f"I have {', '.join(items[:-1])}, and {items[-1]}."
        elif items:
            return f"I have {items[0]}."
        else:
            return "I have nothing."
        
    def failed_memory_to_sentence(self, item:str):
        if item in self.recipe_memory_failed:
            sentence = f"I failed obtaining {item} when you suggested me the following required_items. Please avoid these; "
            for item in self.recipe_memory_failed[item]:
                sentence += f"{item['required_items'] }"
        else:
            sentence = "None"
        return sentence

    def query_wrapper(self, query_item:str)->dict[int]:
        print("\n def query_wrapper is invoked")
        if query_item not in self.item_difficulty:
            self.item_difficulty[query_item] = 5

        system_prompt = """
        Please list the items and their quantities needed to craft items.
        If there are multiple choices, please only pick the easiest one to achieve. 
        If crafting is easier, please set required ingriedients in "required_items".
        If there is no required_items, please set "None" in "required_items".
        If you think it is easier to break blocks to get the item than to craft, please set "None" in "required_items". But crafting is usually easier.
        When you use item name in your answer, use correct item name in Minecraft game.
        Use the python-dict-like format provided in the examples below for your answers.

        Example 1:
        Here is the difficulty list for items (lower = easier):
        planks: 4
        deadbush: 11
        log: 4
        stone_sword: 5
        cobblestone: 5
        crafting_table: 5
        bamboo: 7
        Here is the item description for stick: To craft (1 stick), you need (2 bamboo) with (crafting_table). To craft (4 stick), you need (2 planks) with (crafting_table). You can get (stick) by breaking (deadbush) block without any tool. You can get (stick) by breaking (oak_leaves) block without any tool. You can get (stick) by breaking (spruce_leaves) block without any tool. You can get (stick) by killing (witch). 
        please tell me how to obtain stick.

        Then, pick the easiest one like
        {{"name": "stick", "count": 4, "required_items": {{"planks": 2, "crafting_table": 1}}, "action":"You can craft stick with crafting_table."}}
        
        Example 2: 
        Here is the difficulty list for items (lower = easier):
        planks: 4
        log: 4
        stone_sword: 5
        cobblestone: 5
        stick: 5
        crafting_table: 5
        wooden_pickaxe: 5
        bamboo: 7
        Here is the item description for white_bed: To craft (1 white_bed), you need (3 wool, 3 planks) with (crafting_table). To craft (1 white_bed), you need (1 white_bed, 1 ink_sac) with (crafting_table). To craft (1 white_bed), you need (1 white_bed, 1 lime_dye) with (crafting_table). To craft (1 white_bed), you need (1 white_bed, 1 pink_dye) with (crafting_table). You can get (white_bed) by breaking (white_bed) block with (wooden_pickaxe). 
        please tell me how to obtain white_bed.
        
        Then, pick the easiest one like
        {{"name": "white_bed", "count": 1, "required_items": {{"wool": 3, "planks":3, "crafting_table":1}}, "action":"You can craft white_bed with ingredients."}}

        Example 3:
        Here is the difficulty list for items (lower = easier):
        planks: 4
        log: 4
        stone_sword: 5
        cobblestone: 5
        stick: 5
        crafting_table: 5
        wooden_pickaxe: 5
        bamboo: 8
        Here is the item description for emerald_block: To craft (1 emerald_block), you need (9 emerald) with (crafting_table). You can get (emerald_block) by breaking (emerald_block) block with (iron_pickaxe). 
        please tell me how to obtain emerald_block.
        
        Then, pick the easiest one like
        {{"name": "emerald_block", "count": 1, "required_items": {{"iron_pickaxe": 1}}, "action":"You should break emerald_block with iron_pickaxe."}}


        Note that when you need no materials to get the item, you must answer "None" for "required_items".
        Remember to focus on the format as demonstrated in the examples. 

        When choosing a recipe from multiple options, use the difficulty list provided.
        Prefer items with lower difficulty scores. Avoid using items with high difficulty unless necessary.

        """

        # print(prompt)
        max_request = 5
        inventory = self.inventory_to_sentence()
        error = self.error
        # failed_memory = self.failed_memory_to_sentence(item=query_item)

        while max_request > 0:
            try:
                print("query_item:", query_item)
                query_str = f'Please tell me how to obtain "{query_item}". To get some "{query_item}", you need '
                # Format difficulty info into string
                difficulty_info = "\n".join([
                    f"{item}: {score}" for item, score in sorted(self.item_difficulty.items(), key=lambda x: x[1])
                ]) or "None available yet."

                #* query_itemで検索
                current_dir = os.path.dirname(__file__)
                json_path = os.path.join(current_dir, '..', 'llm', 'data', 'minecraft_data', 'item_key', 'item_dict.json')
                with open(json_path) as f:
                    item_dict = json.load(f)
                
                if query_item in item_dict:
                    item_description = item_dict[query_item]
                else:
                    # raise Exception(f"{query_item} is not in item_dict.json. Please check the file.")
                    #? exceptionではなくwarningに変更
                    print(f"[WARNING] {query_item} is not in item_dict.json. Please check the file.")
                    item_description = "No description available."
                    
                
                #* item_descriptionを使ってpromptを作成
                human_prompt_with_json = (
                    f"This is the current status.\n"
                    f"Inventory: {inventory}\n"
                    f"Nearby block: {self.nearby_block}\n"
                    f"Biome: I am in {self.biome}.\n"
                    f"Error from the last round: {error}\n\n"
                    f"Here is the difficulty list for items (lower = easier):\n"
                    f"{difficulty_info}\n\n"
                    f"Here is the item description for {query_item}:{item_description}\n"
                    f"please tell me how to obtain {query_item}.\n"
                    # f"To get some {query_item}, you need "
                )
                
                print(f"human_prompt_with_json:{human_prompt_with_json}")

                response = self.llm.content(system_prompt=system_prompt, human_prompt=human_prompt_with_json, query_str=query_str, data_dir = "extended_recipe", persist_index=True, use_general_dir=False, search_exist=self.search_switch, similarity_top_k=3)
                # response = self.non_RAG_llm.content(system_prompt=system_prompt, human_prompt=human_prompt_with_json, query_str=query_str, data_dir = "extended_recipe", persist_index=True, use_general_dir=False, similarity_top_k=3)
                
                print("raw response: \n", response)
                
                # print(response)
                # print("\n")
                response = self.extract_dict_from_str(response)
                print("Extracted Dict: \n", response)
                self.check_keys_of_response(response)
                self.item_name_validation(response)
                break
            except Exception as e:
                print(e)
                error = e
                max_request -= 1
                print(f"max_request left {max_request} times")
                continue
        return response




    def resolve_dependency_all(self, init_list: list[str]):
        print("\n def resolve_dependency_all is invoked")

        def build_tree(tree: Tree, node: str, seen_nodes: set):
            """Recursively build the dependency tree"""
            if node in seen_nodes:
                return  # Prevent infinite loops

            seen_nodes.add(node)
            if node in dependency_tree:
                sub_tree = tree.add(f"[cyan]{node}[/cyan]")
                for child in dependency_tree[node]:
                    build_tree(sub_tree, child, seen_nodes)
            else:
                tree.add(f"[white]{node}[/white]")  # Leaf node

        def print_status():
            """Display dependencies as a tree"""
            print("\033[H\033[J", end="")  # Clear terminal
            print("[bold green]✔ Resolved Dependencies:[/bold green]")

            tree = Tree("[green]Root[/green]")
            seen_nodes = set()
            for root in dependency_tree.keys():
                build_tree(tree, root, seen_nodes)

            print(tree)
            sys.stdout.flush()

        def extract_dependencies(new_dependencies, dependency_tree, resolved_edge):
            """
            Extracts dependencies from new_dependencies and updates:
            - dependency_tree (for visualization)
            - unresolved_edge (for next iteration)
            """
            unresolved = []
            for dep in new_dependencies:
                print(f"Processing dependency: {dep}")
                item = dep["name"]
                if item not in dependency_tree:
                    dependency_tree[item] = []

                if isinstance(dep["required_items"], dict):
                    for value in dep["required_items"].keys():
                        if value not in resolved_edge:
                            unresolved.append(value)
                        dependency_tree[item].append(value)

            return list(set(unresolved))  # Remove duplicates before returning

        dependency_list: list[dict] = []
        resolved_edge: list[str] = []
        unresolved_edge: list[str] = init_list
        dependency_tree = {}  # Store parent-child relationships for visualization

        while len(unresolved_edge):
            print_status()
            print(f"unresolved_edge: {unresolved_edge}")

            # Fetch new dependencies using query_wrapper
            new_dependencies = [self.query_wrapper(item) for item in unresolved_edge]
            dependency_list += new_dependencies
            resolved_edge += unresolved_edge

            # Extract and update unresolved dependencies
            unresolved_edge = extract_dependencies(new_dependencies, dependency_tree, resolved_edge)

        print_status()  # Final update
        print("\n[bold green]✅ Dependency Resolution Complete![/bold green]")
        return dependency_list



    def create_recipe_dict(self, dependency_list:list):
        recipe_dict = {}
        for item in dependency_list:
            if item["required_items"] == "None":
                item["required_items"] = None
            recipe_dict[item["name"]] = item
        return recipe_dict

    def reset_recipe(self, all_reset=True, recursive_reset=False, recipe={}):
        if all_reset:
            self.recipe_dependency_list = {}
            print("Reset all recipe dependency")
        else:
            # 再帰的に辿ってレシピをすべて削除
            def recursive_remove(key):
                if key in self.recipe_dependency_list:
                    self.save_faild_recipe({key:1})
                    removed_value = self.recipe_dependency_list.pop(key)
                    print(f"Removed from recipe dependency list: {removed_value}")

                    # このキーを required_items に含む他のアイテムを探索して削除
                    for dependent_key, item in list(self.recipe_dependency_list.items()):
                        if item['required_items'] and key in item['required_items']:
                            recursive_remove(dependent_key)
            
            # 一つ上の親のみ削除
            def remove_direct_dependencies(key):
                if key in self.recipe_dependency_list:
                    self.save_faild_recipe({key:1})
                    removed_value = self.recipe_dependency_list.pop(key)
                    print(f"Removed from recipe dependency list: {removed_value}")

                    # このキーを required_items に直接含むアイテムを削除（再帰しない）
                    for dependent_key, item in list(self.recipe_dependency_list.items()):
                        if item['required_items'] and key in item['required_items']:
                            self.save_faild_recipe({dependent_key:1})
                            removed_value = self.recipe_dependency_list.pop(dependent_key)
                            print(f"Directly removed: {removed_value}")

            for key in recipe:
                if recursive_reset:
                    recursive_remove(key)
                else:
                    remove_direct_dependencies(key)

        self.paths = []
        self.searched_list = []

    def save_success_recipe(self, subgoal:dict):
        for key, value in subgoal.items():
            recipe = self.recipe_dependency_list[key]
            if recipe is not None:
                self.recipe_memory_success[key] = recipe
                if key in self.recipe_data_success:
                    if recipe not in self.recipe_data_success[key]:
                        self.recipe_data_success[key].append(recipe)
                else:
                    self.recipe_data_success[key] = [recipe]
                with open(f"{self.data_path}/recipes_success.json", "w") as f:
                    json.dump(self.recipe_data_success, f, ensure_ascii=False, indent=4)
        self.use_recipe_data_success = True

    def save_faild_recipe(self, subgoal:dict):
        for key, value in subgoal.items():
            if key in self.recipe_memory_failed:
                self.recipe_memory_failed[key].append(self.recipe_dependency_list[key])
            else:
                self.recipe_memory_failed[key] = [self.recipe_dependency_list[key]]
            
            if key in self.recipe_data_success:
                self.use_recipe_data_success = False



    # ========= Current Goal Algorithm ========
    # インベントリとのアイテムの個数の比較
    #そのループの初期のインベントリのアイテムの状態を記録したことですでに取得済みのアイテムに関してもさらに採取できるように変更。
    def get_inventory_diff(self, item_dict:dict, item_name:str):
        if (item_name in self.inventory) and (item_name in self.initial_inventory) :
            diff = item_dict[item_name] - (self.inventory[item_name] - self.initial_inventory[item_name])
            if diff <= 0:
                return 0
            else:
                return diff
        elif item_name in self.inventory:
            diff = item_dict[item_name] - self.inventory[item_name]
            if diff <= 0:
                return 0
            else:
                return diff
        else:
            return item_dict[item_name]

    def current_goal_algorithm(self, task: dict, context="", max_iterations=3):
        print("\ndef current_goal_algorithm is invoked")
        print("\n============= Current Goal Algorithm ==============")
        print(f"task:{task}")
        
        # Visualize self.recipe_dependency_list
        def build_tree(tree: Tree, node: str, highlight_task: str, parent_quantity: int = 1):
            """Recursively build the recipe dependency tree with quantities"""
            if node in self.recipe_dependency_list:
                recipe = self.recipe_dependency_list[node]
                produced_count = recipe.get("count", 1)
                label_quantity = f"(x{produced_count})" if produced_count != 1 else ""
                node_label = (
                    f"[bold red]{node} {label_quantity}[/bold red]" if node == highlight_task
                    else f"[cyan]{node} {label_quantity}[/cyan]"
                )
                sub_tree = tree.add(node_label)

                if recipe.get("required_items") is None:
                    sub_tree.add(f"[white]{node} (x{parent_quantity})[/white]")
                    return

                if isinstance(recipe["required_items"], dict):
                    for child_name, child_qty in recipe["required_items"].items():
                        if child_name in self.recipe_dependency_list:
                            build_tree(sub_tree, child_name, highlight_task, parent_quantity=child_qty)
                        else:
                            sub_tree.add(f"[white]{child_name} (x{child_qty})[/white]")
            else:
                tree.add(f"[white]{node} (x{parent_quantity})[/white]")

        recipe_tree = Tree("[green]Recipe Dependency Tree[/green]")
        for root in self.recipe_dependency_list.keys():
            build_tree(recipe_tree, root, highlight_task=list(task.keys())[0])
        print(recipe_tree)
        print(f"self.recipe_dependency_list:{self.recipe_dependency_list}")

        for name, count in task.items():
            lack_task = self.get_inventory_diff(task, name)
            if lack_task == 0:
                text = f"You already have {task}.\n"
                print(text)
                context += text
                return None, context
            else:
                if name in self.current_goal_memory:
                    if self.iterations > max_iterations:
                        print(f"There might be an infinite loop in recipe dependencies.\n{task}")
                        context = self.recipe_dependency_list[name]["action"]
                        return task, context
                    else:
                        self.iterations += 1
                else:
                    self.current_goal_memory.append(name)

                if name not in self.recipe_dependency_list:
                    self.current_goal_memory = []
                    self.iterations = 0
                    print("\nResolving recipe dependencies...")
                    dependency_list = self.resolve_dependency_all([name])
                    self.recipe_dependency_list = self.create_recipe_dict(dependency_list=dependency_list)

                recipe = self.recipe_dependency_list[name]
                context = recipe["action"]

                if recipe["required_items"] is None:
                    return task, context

                for key, value in recipe["required_items"].items():
                    if name in self.current_goal_memory:
                        required_amount = value
                    else:
                        required_amount = math.ceil(lack_task / recipe['count']) * value

                    lack_ingredients = self.get_inventory_diff({key: required_amount}, key)
                    if lack_ingredients == 0:
                        print(f"You have {key}\n")
                        continue
                    else:
                        print(f"You don't have {key}. Searching more deeply for {key}...\n")
                        next_goal, context = self.current_goal_algorithm({key: required_amount}, context)
                        return next_goal, context

        print(f"You already have all ingredients for {task}.")
        print("\n End============= Current Goal Algorithm ==============")
        return task, context


    def set_current_goal(self, task:dict):
        print("def set_current_goal is invoked")
        print(f"Called set_current_goal: {task}")
        for key, value in task.items():
            print(f"set_current_goal===key:{key} value: {value}====in task.items()")
            #　念の為アイテム名がマインクラフト内に存在するか確認。
            try:
                self.check_item_name(key)
                self.current_goal_memory = []
                self.iterations = 0
                next_goal, context = self.current_goal_algorithm(task)
                return next_goal, context
            except Exception as e:
                print(e)
                error = e
                return None, error
        
            


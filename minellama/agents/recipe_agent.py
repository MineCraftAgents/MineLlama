import json 
from pathlib import Path
import random
import math
import copy

class RecipeAgent:
    def __init__(self,llm=None):
        data_path = ""
        data_path = str(Path(__file__).parent / data_path)
        with open(f"{data_path}/minecraft_dataset/recipes_bedrock.json", "r") as f:
            self.recipe_data = json.load(f)
        with open(f"{data_path}/minecraft_dataset/blocks_bedrock.json", "r") as f:
            self.blocks_data = json.load(f)
        with open(f"{data_path}/minecraft_dataset/dropitems_bedrock.json", "r") as f:
            self.entity_items_data = json.load(f)
        with open(f"{data_path}/minecraft_dataset/harvest_tools.json", "r") as f:
            self.harvest_tools = json.load(f)
        with open(f"{data_path}/minecraft_dataset/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}

        #TODO: 後にレシピルートの選択でLLMを用いる可能性がある。
        self.llm = llm

        self.inventory={}

        self.recipe_dependency_list = {}
        self.searched_list = []
        self.paths = []
        self.goal_items = []
        self.current_goal_memory = []

        self.recipe_memory_success = {}
        self.recipe_memory_failed = {}

        self.iterations = 0
    
    # item名がMinecraftに存在するかどうか判定
    def check_item_name(self, name:str):
        if name in self.mc_items:
            return True
        else:
            print(f"Couldn't find name in Minecraft game: {name}")
            return False
        
    def complete_checker(self, goal:dict):
        for key in list(goal.keys()):
            diff = self.get_inventory_diff(goal, key)
            if diff == 0:
                done = True
            else:
                done = False
                return done
        return done

    # inventoryのアップデート。item名を整形し、統合する。
    def update_inventory(self, inventory:dict):
        log_list = ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log"]
        planks_list = ["oak_planks", "birch_planks", "spruce_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "mangrove_planks"]
        self.inventory = copy.deepcopy(inventory)
        inventory_keys = list(self.inventory.keys())
        log_count = 0
        planks_count = 0
        for key in inventory_keys:
            if key in log_list:
                log_count += self.inventory[key]
                self.inventory.pop(key)
            elif key in planks_list:
                planks_count += self.inventory[key]
                self.inventory.pop(key)

        if log_count > 0 :
            self.inventory["log"] = log_count
        if planks_count > 0 :
            self.inventory["planks"] = planks_count
            
        print(f"Updated Inventory: {self.inventory}\n")

    # ========= geratate context =========
    #　必要なツールを探す。inventoryに入っていたらそのツールを、入っていなければ最も簡単なツールを示す。ツールが必要なければNoneを返す
    def required_tool(self, block_name:str):
        tools = None
        if block_name in self.harvest_tools:
            tools = self.harvest_tools[block_name]['harvestTools']

        if tools is None:
            return None
        else:
            for tool in tools:
                if tool in self.inventory:
                    return tool
            return tools[0]

    #　コンテクスト作成。採取に必要なツール、または殺す必要のあるエンティティ
    def get_context(self, item:str):
        context_text = ""
 
        if item in self.blocks_data:
            blocks = self.blocks_data[item]
            for block in blocks:
                harvest_tool = self.required_tool(block["name"])
                if harvest_tool is None:
                    harvest_tool = "no tool"
                context_text += f"You can get {item} by breaking {block['name']}. You need {harvest_tool} to break it.\n"
        
        if item in self.harvest_tools:
            harvest_tool = self.required_tool(item)
            if harvest_tool is None:
                harvest_tool = "no tool"
            text = f"You can get {item} by breaking {item}. You need {harvest_tool} to break it.\n"
            if text not in context_text:
                context_text += text

        if item in self.entity_items_data:
            entity = self.entity_items_data[item]
            entity_text = ", ".join(entity)
            context_text += f"You can get {item} by killing {entity_text}. \n"

        if item in self.recipe_dependency_list:
            if self.recipe_dependency_list[item] is not None:
                tool = self.recipe_dependency_list[item]['type']
                if tool == "crafting_table":
                    context_text += f"You can get {item} by crafting with {tool}."
                elif tool == "furnace":
                    context_text += f"You can get {item} by smelting with {tool}."
        return context_text



    # ========= recipe dependencies ========
    #　ランダムにレシピを選ぶ
    def search_recipe(self, name:str):
        if name in self.searched_list:
            recipe=None
        else:
            self.searched_list.append(name)
            if name in self.recipe_data:
                # 成功リストに存在する場合は、そちらを使う
                if name in self.recipe_memory_success:
                    recipe = self.recipe_memory_success[name]
                #　成功リストにない場合はランダムに選ぶ
                else:
                    # recipeはリスト, [{'count': 1, 'type': 'crafting_table', 'ingredients': {'bamboo': 2}}, {'count': 4, 'type': 'crafting_table', 'ingredients': {'planks': 2}}]
                    # ランダムに選択
                    recipe = random.choice(self.recipe_data[name])
                    # 失敗リストにあるものは除外する
                    if name in self.recipe_memory_failed:
                        for _ in range(3):
                            if recipe not in self.recipe_memory_failed[name]:
                                break
                            print(f"This recipe was failed before. Pick randomly again: {recipe}")
                            recipe = random.choice(self.recipe_data[name])
            else:
                # recipeデータセットに存在しない場合
                recipe =  None
            self.recipe_dependency_list[name] = recipe
        return recipe
    
    #　依存関係を取得
    def recipe_dependency(self, name:str):
        recipe = self.search_recipe(name)
        if recipe is not None:
            for ingredient_name in recipe["ingredients"]:
                self.recipe_dependency(ingredient_name)
        self.searched_list = []
    

    # レシピのルートを可視化
    def get_recipe_paths(self, item:str, count:int, visited=None):
        recipe_dict=self.recipe_dependency_list
        if visited is None:
            visited = set()
        if item in visited:
            return [[{item:count}]]  # Avoid infinite loops

        visited.add(item)

        if recipe_dict[item] is None:
            return [[{item:count}]]

        expanded_paths = []
        current_path = [{item:count}]
        for key, value in recipe_dict[item]['ingredients'].items():
            required_amount = math.ceil(count / recipe_dict[item]['count']) * value
            sub_paths = self.get_recipe_paths(key, required_amount, visited.copy())
            for sub_path in sub_paths:
                expanded_paths.append(current_path + sub_path)
        return expanded_paths
    
    #  def get_recipe_paths(self, item:str, visited=None):
    #     recipe_dict=self.recipe_dependency_list
    #     if visited is None:
    #         visited = set()
    #     if item in visited:
    #         return [[item]]  # Avoid infinite loops

    #     visited.add(item)

    #     if recipe_dict[item] is None:
    #         return [[item]]

    #     expanded_paths = []
    #     current_path = [item]
    #     for ingredient in recipe_dict[item]['ingredients']:
    #         sub_paths = self.get_recipe_paths(ingredient, visited.copy())
    #         for sub_path in sub_paths:
    #             expanded_paths.append(current_path + sub_path)
    #     return expanded_paths
    
    
    def reset_recipe(self):
        self.recipe_dependency_list = {}
        self.paths = []

    # レシピルート取得　&　可視化
    def get_recipe_list(self, item_name:str, reset=False):
        if reset:
            self.reset_recipe()

        self.recipe_dependency(item_name)
        #TODO :count
        self.paths = self.get_recipe_paths(item_name,1) + self.paths

        # show results
        print(f"Goal Item: {item_name}")
        print("\nrecipe_dependency_list:")
        for key, value in self.recipe_dependency_list.items():
            print(f"{key}: {value}")
        print("\nPaths:")
        # print(self.paths)
        # for goal_item in self.paths:
        #     for path in goal_item:
        #         string_path = [f"{list(d.keys())[0]}: {list(d.values())[0]}" for d in path]
        #         print(" -> ".join(string_path))
        for goal_item in self.paths:
            print(goal_item)


    # ========= Current Goal Algorithm ========
    # インベントリとのアイテムの個数の比較
    def get_inventory_diff(self, item_dict:dict, item_name:str):
        if item_name in self.inventory:
            diff = item_dict[item_name] - self.inventory[item_name]
            if diff <= 0:
                return 0
            else:
                return diff
        else:
            return item_dict[item_name]



    def current_goal_algorithm(self, task:dict, max_iterations=3):
        print("\n============= Current Goal Algorithm ==============")
        print(task)
        for name, count in task.items():
            if self.get_inventory_diff(task,name) == 0:
                print(f"You already have {task}.\n")
                return None
            else:
                # 無限ループの判定
                if name in self.current_goal_memory:
                    # とりあえず3回までの繰り返しは認める。なぜなら、レシピが複雑になれば、一つのルートで同じアイテムが複数回必要になる可能性もあるため。
                    if self.iterations > max_iterations:
                        print(f"There might be an infinit loop in recipe dependencies.\n{task}")
                        # 無限ループがある場合は、切り上げて、アイテムの採取に取り掛かる。その際、必要なツールがあるか検索。
                        if name in self.blocks_data:
                            block = random.choice(self.blocks_data[name])
                            tool_to_mine = self.required_tool(block["name"])
                        #TODO: diamond_oreのケース
                        elif name in self.harvest_tools:
                            tool_to_mine = self.required_tool(name)
                        else:
                            tool_to_mine = None

                        if tool_to_mine is None or tool_to_mine in self.inventory:
                            print("You can collect it now.")
                            return task
                        else:
                            print(f"Craft a tool to mine first: {tool_to_mine}")
                            next_goal = self.current_goal_algorithm({tool_to_mine:1})
                            return next_goal
                    else:
                        self.iterations += 1
                else:
                    self.current_goal_memory.append(name)

                if name not in self.recipe_dependency_list:
                    # 無限ループmemoryはリセット
                    self.current_goal_memory = []
                    self.iterations = 0
                    self.get_recipe_list(name)
                    
                recipe = self.recipe_dependency_list[name] #辞書型{'count': 1, 'type': 'crafting_table', 'ingredients': {'iron_ingot': 3, 'stick': 2}}
                # recipeがNoneなら、スタートノードであるということ。探索を行う。その前に、必要な採取ツールがあるか確認する。
                if recipe is None:
                    #TODO: ブロックをどのようにして選ぶか。とりあえずランダムに選ぶ。
                    if name in self.blocks_data:
                        block = random.choice(self.blocks_data[name])
                        tool_to_mine = self.required_tool(block["name"])
                    #TODO: diamond_oreのケース
                    elif name in self.harvest_tools:
                        tool_to_mine = self.required_tool(name)
                    else:
                        tool_to_mine = None

                    if tool_to_mine is None or tool_to_mine in self.inventory:
                        print("You can collect it now.")
                        return task
                    else:
                        print(f"Craft a tool to mine first: {tool_to_mine}")
                        next_goal = self.current_goal_algorithm({tool_to_mine:1})
                        return next_goal

                for key, value in recipe["ingredients"].items():
                    if self.get_inventory_diff(recipe["ingredients"],key) == 0:
                        print(f"You have {key}\n")
                    else:
                        print(f"You don't have {key}. Searching more deeply for {key}...\n")
                        self.goal_items = [{key:value}] + self.goal_items
                        next_goal = self.current_goal_algorithm({key:value})
                        return next_goal
                
                print(f"You already have all ingredients to craft {task}. ")
                tool_to_craft = self.recipe_dependency_list[name]["type"] # crafting_table or furnace
                #TODO: とりあえずfurnaceのときのみ作成。crafting_tableはアクション関数に組み込んで自動で作成。crafting_tableなしでつくれるアイテムの判定ができないため。
                if tool_to_craft == "furnace":
                    print(f"You have to craft {tool_to_craft} first.")
                    next_goal = self.current_goal_algorithm({tool_to_craft:1})
                    return next_goal
                else:
                    print(f"Please craft {task}.")
                    return task

    def set_current_goal(self, task:dict):
        print(f"Called set_current_goal: {task}")

        for key, value in task.items():
            if self.check_item_name(key):
                self.current_goal_memory = []
                self.iterations = 0
                next_goal = self.current_goal_algorithm(task)
                return next_goal
            else:
                return None
        
        


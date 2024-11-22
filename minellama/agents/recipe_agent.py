import json 
from pathlib import Path
import random
import math
import re
import copy

class RecipeAgent:
    def __init__(self,llm=None):
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
    def get_context(self, item:str, method=None):
        context_text = ""

        if method == "mine" or method is None:
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

        if method == "craft" or method is None:
            if item in self.recipe_dependency_list:
                if self.recipe_dependency_list[item] is not None:
                    tool = self.recipe_dependency_list[item]['type']
                    if tool == "crafting_table":
                        context_text += f"You can get {item} by crafting with {tool}."
                    elif tool == "furnace":
                        for key, value in self.recipe_dependency_list[item]["ingredients"].items():
                            context_text += f"You can get {item} by smelting {key} with {tool}."
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
                if name in self.recipe_data_success and self.use_recipe_data_success:
                    recipe = random.choice(self.recipe_data_success[name])
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
    
    
    def extract_dict_from_str(self,response:str)->dict:
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            return json.loads(json_dict.replace("'", '"'))
        else:
            raise Exception("No json dict found. Trying again.")    

    #　LLMを使用して現在いるバイオームに適したレシピを選択する
    def recipe_choose_by_llm(self, biome:str, name:str, max_iterations=10):
        if name in self.searched_list:
            recipe=None
        else:
            self.searched_list.append(name)
            if name in self.recipe_data:
                system_prompt = """
                You are an AI that supports Minecraft play.
                You are responsible for selecting the appropriate recipe for crafting items in Minecraft for the biome in which the player is currently located.
                Based on the information you are given and the recipe, if the item in the recipe is specific to the biome you are in and you are able to collect it, you will collect it,
                If not, then select an item that can be collected in any biome (i.e., not specific to any biome), and so on.
                The output should be a single element from the list of recipes given.

                The information to be passed is as follows
                BIOME: The biome the player is currently in.
                RECIPE_LIST: The list of recipes the player is currently reviewing. You must select one of these recipes. The format is [{{"count": 1, "type": "crafting_table", "ingredients": {{"bamboo": 2}}}}, {{"count": 4, "type": "crafting_table", 'ingredients": {{"planks": 2}}}}] where the "ingredients" part is the part of the required ingredients that you will match with the biome information.

                Examples of judgments are as follows
                Example 1:
                BIOME:jungle
                RECIPE_LIST:[{{"count": 1, "type": "crafting_table", "ingredients": {{"bamboo": 2}}}}, {{{{"count": 4, "type": "crafting_table", "ingredients": {{" planks": 2}}}}]
                DESCRIPTION: In the jungle biome, bamboo is growing and can be collected. Therefore, we will collect the biome-specific item, bamboo, here.
                Output: {{"count": 1, "type": "crafting_table", "ingredients": {{"bamboo": 2}}}}

                Example 2:
                BIOME:taiga
                RECIPE_LIST:[{{"count": 1, "type": "crafting_table", "ingredients": {{"melon_seeds": 2}}}}, {{"count": 4, "type": "crafting_table", "ingredients": {{"planks": 2}}}} {{"planks": 2}}}}, {{"count": 4, "type": "crafting_table", "ingredients": {{"cactus": 2}}}}]
                Explanation: In the taiga biome, neither melon_seeds nor cactus are growing, so they cannot be collected. On the other hand, they can be collected in the desert biome. Therefore, these items are specific to other biomes and cannot be collected in the current biome. Therefore, here we use planks that are not specific to any biome and can be procured anywhere.
                Output: {{"count": 4, "type": "crafting_table", "ingredients": {{"planks": 2}}}}

                The following are precautions for the output. Please be sure to follow them.
                1. The output should be a single element in the given list of recipes as it is. Example: {{"count": 4, "type": "crafting_table", "ingredients": {{"planks": 2}}}}
                2. Only the final recipe is to be output as the answer. No other explanations are needed. No other explanations, etc. are needed.
                3. It is forbidden to modify the given recipe and output it without permission.
                4. Use double quotes when you write the property name of the dict in answer.
                """
                iterations = 0
                error = "None"
                print("Choosing recipe by LLM...")
                while iterations < max_iterations:
                    extracted_response = None #初期化をかけておく
                    human_prompt_biome = f"BIOME: {biome}, RECIPE_LIST: {self.recipe_data[name]}, which recipe should be done? Error from the last round: {error}"
                    try :
                        response = self.llm.content(system_prompt, query_str=human_prompt_biome, data_dir="recipe")
                        extracted_response = self.extract_dict_from_str(response)
                        if extracted_response is not None: 
                            for item in extracted_response["ingredients"].keys():
                                if item in self.mc_items:      
                                    self.recipe_dependency_list[name] = extracted_response
                                    return extracted_response   
                                else:
                                    raise Exception(f"There is no item called {item}.\n")
                        else:
                            raise Exception("Invalid Error. No dict found.")
                    except Exception as e :
                        error = e
                        print(f"\nFormat was invalid. {e} \n")
                        iterations += 1
                #規定回数で正しい回答を出せなかった場合
                if iterations >= max_iterations:
                    print("The number of iteration reached the limit. Choosing a recipe randomly...")
                    recipe= self.search_recipe(name=name)
            else:
                # recipeデータセットに存在しない場合
                recipe = None
        self.recipe_dependency_list[name] = recipe
        return recipe
            
        
    #　依存関係を取得
    def recipe_dependency(self, name:str):
        recipe = self.recipe_choose_by_llm(self.biome, name)
        #recipe = self.search_recipe(name)
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
    
    def reset_recipe(self):
        self.recipe_dependency_list = {}
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


    # レシピルート取得　&　可視化
    def get_recipe_list(self, item_name:str, reset=False):
        if reset:
            self.reset_recipe()

        self.recipe_dependency(item_name)
        #biome :count
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

    #get_recipe_listメソッドでの結果を返すようにした関数。printだけ省いているがほかは同じ。
    def get_recipe_list_for_export(self, item_name:str, reset=False):
        if reset:
            self.reset_recipe()

        self.recipe_dependency(item_name)
        #biome :count
        self.paths = self.get_recipe_paths(item_name,1) + self.paths

        # show results
        for key, value in self.recipe_dependency_list.items():
            print(f"{key}: {value}")
        return self.paths


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
#保存用。
    # インベントリとのアイテムの個数の比較
    # def get_inventory_diff(self, item_dict:dict, item_name:str):
    #     if item_name in self.inventory:
    #         diff = item_dict[item_name] - self.inventory[item_name]
    #         if diff <= 0:
    #             return 0
    #         else:
    #             return diff
    #     else:
    #         return item_dict[item_name]

    def current_goal_algorithm(self, task:dict, context="", max_iterations=3):
        print("\n============= Current Goal Algorithm ==============")
        print(task)
        for name, count in task.items():
            # taskのアイテムの不足分
            lack_task = self.get_inventory_diff(task,name)
            if lack_task == 0:
                text = f"You already have {task}.\n"
                print(text)
                context += text
                return None, context
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
                        #biome: diamond_oreのケース
                        elif name in self.harvest_tools:
                            tool_to_mine = self.required_tool(name)
                        else:
                            tool_to_mine = None

                        if tool_to_mine is None or tool_to_mine in self.inventory:
                            text = f"You can collect {name} now.\n"
                            print(text)
                            context += text
                            context += self.get_context(name, method="mine")
                            return task, context
                        else:
                            print(f"Craft a tool to mine first: {tool_to_mine}")
                            next_goal, context = self.current_goal_algorithm({tool_to_mine:1}, context)
                            return next_goal, context
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
                    #biome: ブロックをどのようにして選ぶか。とりあえずランダムに選ぶ。
                    if name in self.blocks_data:
                        block = random.choice(self.blocks_data[name])
                        tool_to_mine = self.required_tool(block["name"])
                    #biome: diamond_oreのケース
                    elif name in self.harvest_tools:
                        tool_to_mine = self.required_tool(name)
                    else:
                        tool_to_mine = None

                    if tool_to_mine is None or tool_to_mine in self.inventory:
                        text = f"You can collect {name} now.\n"
                        print(text)
                        context += text
                        context += self.get_context(name, method="mine")
                        return task, context
                    else:
                        print(f"Craft a tool to mine first: {tool_to_mine}")
                        next_goal, context= self.current_goal_algorithm({tool_to_mine:1}, context)
                        return next_goal, context

                # recipeが存在する場合は、材料をチェックする。
                for key, value in recipe["ingredients"].items():
                    #　材料の不足数
                    if name in self.current_goal_memory:
                        # self.current_goal_memoryに入っている場合は、無限ループの可能性があり、必要数を乗算すると非常に大きな値になってしまうため、デフォルト値を使う。
                        required_amount = value
                    else:
                        required_amount = math.ceil(lack_task / recipe['count']) * value
                    lack_ingredients = self.get_inventory_diff({key:required_amount},key)
                    if  lack_ingredients == 0:
                        print(f"You have {key}\n")
                    else:
                        print(f"You don't have {key}. Searching more deeply for {key}...\n")
                        # self.goal_items = [{key:value}] + self.goal_items
                        next_goal, context = self.current_goal_algorithm({key:required_amount}, context)
                        return next_goal, context
                
                print(f"You already have all ingredients to craft {task}. ")

                tool_to_craft = self.recipe_dependency_list[name]["type"] # crafting_table or furnace
                #biome: とりあえずfurnaceのときのみ作成。crafting_tableはアクション関数に組み込んで自動で作成。crafting_tableなしでつくれるアイテムの判定ができないため。
                if tool_to_craft is not None  and  tool_to_craft not in self.inventory  and  name not in self.items_without_crafting_table:
                    print(f"You have to craft {tool_to_craft} first.")
                    next_goal, context = self.current_goal_algorithm({tool_to_craft:1}, context)
                    return next_goal, context
                else:
                    text = f"You alreaday have all ingredients and tools. Please craft or smelt {task}.\n"
                    print(text)
                    context += text
                    context += self.get_context(name, method="craft")
                    return task, context

    def set_current_goal(self, task:dict):
        # print(f"Called set_current_goal: {task}")

        for key, value in task.items():
            #　念の為アイテム名がマインクラフト内に存在するか確認。
            if self.check_item_name(key):
                self.current_goal_memory = []
                self.iterations = 0
                next_goal, context = self.current_goal_algorithm(task)
                return next_goal, context
            else:
                error = f"There is no such item in Minecraft: {key}"
                print(error)
                return None, error
        
        


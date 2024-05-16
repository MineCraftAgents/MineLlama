import copy
from ..control_primitives import load_control_primitives
from ..llm import Llama2

class DecisionMaker:
    def __init__(self):
        self.inventory = {}
        self.control_primitives = load_control_primitives()
        # self.control_primitives = []
        self.recipes = []
        # self.llm_7b = Llama2(name="meta-llama/Llama-2-7b-chat-hf")
        # self.llm_70b = Llama2(name="meta-llama/Llama-2-70b-chat-hf")
    
    @property
    def programs(self):
        programs = ""
        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"
        return programs

    def update_inventory(self, inventory):
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
            
        print("Updated Inventory:\n", self.inventory)

    def check_diff(self, root, item):
        if item in self.inventory:
            diff = root[item] - self.inventory[item]
            if diff <= 0:
                return 0
            else:
                return diff
        else:
            return root[item]

    def check_if_start_node(self, node):
        start_nodes = ["log", "cobblestone", "dirt", "raw_iron","white_wool", "beef"]
        if node in start_nodes:
            return True
        else:
            return False
        
    def search_tree(self, item):
        #==============Recipe trees by Llama2
        recipe_list = {
            "stone_pickaxe":{"stick":2, "cobblestone":3, "crafting_table":1},
            "stick":{"planks":2},
            "planks":{"log":1},
            "wooden_pickaxe":{"stick":2, "planks":3, "crafting_table":1},
            "iron_pickaxe":{"stick":2, "iron_ingot":3, "crafting_table":1},
            "iron_ingot":{"raw_iron":1,"furnace":1},
            "white_bed":{"planks":3,"white_wool":3, "crafting_table":1},
            "cooked_beef":{"beef":1,"furnace":1},
            "furnace":{"cobblestone":8, "crafting_table":1},
            "crafting_table":{"planks":4}
        }
        #===================================

        if item in recipe_list:
            recipe = recipe_list[item]
            return recipe
        else:
            print("No recipe: ", item)
            return

    def search_tree_by_llama2(self, item):
        print(f"I am searching tree of {item}...\n")
        print(f"Here is current recipe list: \n {self.recipes}")

        for recipe in self.recipes:
            if item in recipe:
                print("Got recipe from the list.")
                return recipe[item]
            
        responses = self.llm.get_recipe(item)
        print("RESPONSES BY LLAMA: ",responses)
        for response in responses:
            key, value = response.popitem()
            if key == item:
                tree = value
            # for recipe in self.recipes:
            #     if key in recipe:
            #         print("Already in the recipes list: ", key)
            #     else:
            self.recipes.append({key:value})
            print("Added to the recipes list: ", key)
        return tree
    

    def required_tool(self, item):
        minable_with_woodenpickaxe =["cobblestone","coal"]
        minable_with_stonepickaxe = ["raw_iron"]
        minable_with_ironpickaxe = ["diamond_ore"]
        if item in minable_with_woodenpickaxe:
            return {"wooden_pickaxe":1}
        elif item in minable_with_stonepickaxe:
            return {"stone_pickaxe":1}
        elif item in minable_with_ironpickaxe:
            return {"iron_pickaxe":1}
        else:
            return None
    
            
    def reset_memory(self):
        return
        
    def complete_checker(self, goal:dict):
        for key in list(goal.keys()):
            diff = self.check_diff(goal, key)
            if diff == 0:
                done = True
            else:
                done = False
                return done
        return done
   
    # Get item by mining or killing
    def action_code_generator(self, goal:dict):
        minable = ["log","dirt"]
        animals = {"beef":"cow", "raw_chicken":"chicken", "raw_porkchop":"pig", "white_wool":"sheep"}
        key = list(goal.keys())[0]
        count = goal[key]
        required_tool = self.required_tool(key)
        if required_tool is None:
            if key in minable:
                code = f"await mine(bot, '{key}',{count});"
            elif key in animals.keys():
                code = f"await kill(bot, '{animals[key]}', {count});"
            else:
                print("Could not find the item in the dicts in action_code_generator.")
                return
        else:
            code = f"await mine(bot, '{key}',{count},'{list(required_tool.keys())[0]}');"
        return code
    

    # Craft or smelt
    def craft_code_generator(self, goal:dict):
        smelt_items = ["iron_ingot", "cooked_beef","cooked_porkchop"]
        key = list(goal.keys())[0]
        count = goal[key]
        if key in smelt_items:
            furnace_diff = self.check_diff({'furnace':1}, 'furnace')
            if furnace_diff == 0:
                ingredients = list(self.search_tree(key).keys())[0]
                coal_diff = self.check_diff({'planks':1}, 'planks')
                if coal_diff == 0:   
                    code = f"await smelt(bot,'{ingredients}',{count},'planks');"
                else:
                    return "fuel"
            else:
                return "furnace"
        else:
            code = f"await craft(bot,'{key}',{count});"
        return code



    def set_current_goal(self, next_task:dict):
        goals = next_task
        if len(goals) == 0:
            print("The goals dict is empty at set_current_goal func.")
            return None
        
        for goal in goals.keys():
            if self.check_diff(goals, goal) == 0:
                print(f"You already have {goal}.\n")
            else:
                #レシピ探索
                root = self.search_tree(goal)
                for node in root.keys():
                    #the difference between requirement and inventory
                    node_diff = self.check_diff(root, node)
                    #if satisfied
                    if node_diff == 0:
                        print(f"Goal: {goal} \nRoot: {root} \nYou have {node}\n")
                    else:
                        #start node or not スタートノードなら採集
                        if self.check_if_start_node(node):
                            print(f"Goal: {goal} \nRoot: {root} \nYou don't have {node}, and it is a start node. Please collect the item. \n")
                            print({node:root[node]})
                            #採集するのにアイテムが必要か
                            required_tool = self.required_tool(node)
                            if required_tool is None:
                                code = self.action_code_generator({node:root[node]})
                            else:
                                tool_diff = self.check_diff(required_tool, list(required_tool.keys())[0])
                                print(f"You need {list(required_tool.keys())[0]} to get {node}.\n")
                                #ツールがあれば採集。なければ作る。
                                if tool_diff == 0:
                                    print(f"You already have the required tool: {required_tool}\n")
                                    code = self.action_code_generator({node:root[node]})
                                else:
                                    print(f"You have to craft {required_tool}.\n")
                                    code = self.set_current_goal(required_tool)
                            return code
                        # If it's not start node, explore the next tree more deeply
                        else:
                            print(f"Goal: {goal} \nRoot: {root} \nYou don't have {node}, and you have to craft it. Searching more deeply for {node}...\n")
                            code = self.set_current_goal({node:root[node]})
                            return code

        #All items are satisfied, then craft or smelt
        print(f"You already have all ingredients of {goals}.\n")
        print(f"Please craft {goals}.")
        code = self.craft_code_generator(goals)
        if code == "furnace":
            code = self.set_current_goal({'furnace':1})
        elif code =='fuel':
            code = self.set_current_goal({'planks':1})
        return code

        # root = self.search_tree(goal)
        # for node in root.keys():
        #     if self.check_diff(root, node):
        #         pass
        #     else:
        #         if self.check_start_node(node):
        #             return node
        #         else:
        #             return self.set_current_goal(node)
        #     return node


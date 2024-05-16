import copy
from ..control_primitives import load_control_primitives
from ..llm import Llama2,GPT

class DecisionMakerLLM:
    def __init__(self, llm:str, llm_model:str="", hf_auth_token:str="", local_llm_path:str=None):
        self.inventory = {}
        self.control_primitives = load_control_primitives()
        # self.control_primitives = []
        self.recipes = {}
        if llm == "llama":
            self.llm = Llama2(hf_auth_token=hf_auth_token, name=llm_model, local_llm_path=local_llm_path)
        elif llm == "gpt":
            self.llm = GPT(llm_model=llm_model)
        self.memory = {}
        self.current_context = ""
        self.current_code = ""
        self.search_tree_iteration = 0
    
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
            
        print(f"Updated Inventory: {self.inventory}\n")

    def check_diff(self, root, item):
        if item in self.inventory:
            diff = root[item] - self.inventory[item]
            if diff <= 0:
                return 0
            else:
                return diff
        else:
            return root[item]

    ## Get recipe without asking LLM.
    # def search_tree(self, item):
    #     #==============Recipe trees
    #     recipe_list = {
    #         "stone_pickaxe":{"stick":2, "cobblestone":3, "crafting_table":1},
    #         "stick":{"planks":2},
    #         "planks":{"log":1},
    #         "wooden_pickaxe":{"stick":2, "planks":3, "crafting_table":1},
    #         "iron_pickaxe":{"stick":2, "iron_ingot":3, "crafting_table":1},
    #         "iron_ingot":{"raw_iron":1,"furnace":1,"planks":2},
    #         "white_bed":{"planks":3,"white_wool":3, "crafting_table":1},
    #         "cooked_beef":{"beef":1,"furnace":1,"planks":2},
    #         "furnace":{"cobblestone":8, "crafting_table":1},
    #         "crafting_table":{"planks":4},
    #         "raw_iron":{"stone_pickaxe":1},
    #         "cobblestone":{"wooden_pickaxe":1},
    #         "log":None,
    #         "beef":None,
    #         "white_wool":None,
    #     }
    #     #===================================

    #     if item in recipe_list:
    #         recipe = recipe_list[item]
    #         return recipe
    #     else:
    #         print("No recipe: ", item)
    #         return
    
    # Correct the name of item because LLM often makes mistakes
    def item_name_checker(self, recipe:dict):
        if recipe is None:
            return recipe
        
        if "logs" in recipe:
            recipe["log"] = recipe.pop("logs")
        if "plank" in recipe:
            recipe["planks"] = recipe.pop("plank")
        if "sticks" in recipe:
            recipe["stick"] = recipe.pop("sticks")
        return recipe

    def search_tree(self, item):
        # When failing too many times, reset the recipe.
        if self.search_tree_iteration > 20:
            self.recipes = {}
            print("Too many iterations. Reset the recipes list.")
            self.search_tree_iteration = 0
            
        self.search_tree_iteration += 1
        print(f"I am searching tree of {item}...\n")
        print(f"Here is current recipe list: \n {self.recipes}")

        if item in self.recipes:
            print("Got recipe from the list.")
            return self.recipes[item]
            
        recipe_list = self.llm.get_recipe([item])
        recipe_list = self.item_name_checker(recipe_list)
        print("RESPONSES BY LLAMA: ",recipe_list)
        for key in list(recipe_list.keys()):
            requirements = recipe_list[key]
            self.recipes[key] = self.item_name_checker(requirements)
            print("Added to the recipes list: ", key)
        return self.recipes[item]
    

    def save_action(self, subgoal, code):
        self.memory[str(subgoal)] = code
        print(f"Saved new code: {self.memory}\n")
        return
    
    def reset_memory(self):
        self.memory = {}
        
    def complete_checker(self, goal:dict):
        for key in list(goal.keys()):
            diff = self.check_diff(goal, key)
            if diff == 0:
                done = True
            else:
                done = False
                return done
        return done
    
    def code_generator(self, goal, retrieval=False, error_massage=""):
        if retrieval:
            if str(goal) in self.memory:
                code = self.memory[str(goal)]
                print(f"\nRetrieved code from memory:  {code}\n")
                return code
        # context = self.llm.get_context(task=goal)
        code = self.llm.generate_action(task=goal,index_dir="context")

        # self.current_context = context
        self.current_code = code
        self.search_tree_iteration = 0
        return code
    

    def set_current_goal(self, next_task:dict):
        print("\n=============CurrentGoalAlgorithm==============")
        goals = next_task
        if len(goals) == 0:
            print("The goals dict is empty at set_current_goal func.")
            return None
        
        for goal in goals.keys():
            if self.check_diff(goals, goal) == 0:
                print(f"You already have {goal}.\n")
            else:
                #Search recipe tree
                root = self.search_tree(goal)
                print(f"Goal: {goal} \nRoot: {root}\n")
                if root is None:
                    print("You can collect it now.")
                    return goals
                for node in root.keys():
                    #the difference between requirement and inventory
                    node_diff = self.check_diff(root, node)
                    #if satisfied
                    if node_diff == 0:
                        print(f"You have {node}\n")
                    else:
                        print(f"You don't have {node}. Searching more deeply for {node}...\n")
                        next_goal = self.set_current_goal({node:root[node]})
                        return next_goal

        #All items are satisfied, then craft or smelt
        print(f"You already have all ingredients of {goals}.\n")
        print(f"Please craft {goals}.")
        return goals



import re
import json
from pathlib import Path


# role_explanation = """
# You are a smith, who mainly create iron_pickaxe.
# """


class RoleAgent:
    def __init__(self, llm):
        self.llm = llm

        data_path = ""
        data_path = str(Path(__file__).parent / data_path)
        with open(f"{data_path}/minecraft_dataset/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}

        self.role_prompt = """
        You are playing a role in Minecraft game.
        I want you to plan the next task.
        Each time, I give you information below:
        Role: ... ;This is your role in Minecraft.
        Invenotory: {{"ITEM_NAME":COUNT,...}}
        Memory: [{{"TASK":COUNT}},...] ;Those are the tasks you achieved before.

        You must follow the python-dict like format below when you answer:
        {{"ITEM_NAME":COUNT}}

        Here is an example:
        {{"diamond_sword":3}}
        """

    def extract_dict_from_str(self,response):
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            # print("json_dict: ",json_dict)
            return json.loads(json_dict)
        else:
            print("No json dict found. Trying again.")
            raise Exception("Invalid Format Error")

    def item_name_checker(self, json_dict):
        name = list(json_dict.keys())[0]
        if name == "logs":
            task = {"log":json_dict[name]}
        if name == "plank":
            task = {"planks":json_dict[name]}
        if name == "sticks":
            task = {"stick":json_dict[name]}
        else:
            task = {name:json_dict[name]}
        return task

    def check_item_name(self, name:str):
        if name in self.mc_items:
            print(self.mc_items[name])
            return True
        else :
            return False

    def make_todaysgoal(self, dream, inventory, memory):
        print("~~~~~~~~~~make_todaysgoal~~~~~~~~~~~")
        system_prompt = """
        You are assisting with role-playing in the Minecraft game.

        To complete a role, you need to achieve a specific item set. Your task is to translate the given role text into a final item list (in Python dictionary format) that represents the goal.

        Each time, you will be given:

        Role: This is the role the player has been assigned.
        Inventory: {{"ITEM_NAME":COUNT,...}} — These are the items the player currently has.
        Memory: [{{"TASK":COUNT}},...] — These are the tasks you have completed before.
        Your goal is to determine and output the final item list that the player should have to complete the given role. The output should be in the following format:
        {{"ITEM_NAME":COUNT,...}}

        Please follow these instructions:

        1.Use accurate Minecraft item names and avoid ambiguous terms (e.g., fertilizer, animal, food, tool, material).
        2.Provide your answers in the format of a Python dictionary with the item names and their quantities. Example: {{"diamond_sword":3}}
        3.Only provide the answer in the specified format and do not include additional explanations or comments.
        4.Please do not include line breaks between elements in the list of answers.
        """
        
        human_prompt = f"Role: {dream} Inventory: {inventory} Memory: {memory}, what does the player have to get to complete role playing? "
        
        print("dream:", dream)
        
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="recipe")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        
        checked = []
        i = 0
        for item in extracted_response:
            print(item)
            if self.check_item_name(item):
                print(f"{item} is a correct minecraft item name")
                checked.append(extracted_response[i])
            i = i + 1
        
        print("checked response : ", checked)
        # print(extracted_response)
        return checked
    
    def next_task(self, role, todaysgoal, inventory, memory=None):
        print("~~~~~~~~~~next task~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Role: {role} Inventory: {inventory} Memory: {memory} What is the next task?"
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="action")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        # print(extracted_response)
        return extracted_response
    

        
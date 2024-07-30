import re
import json

# role_explanation = """
# You are a smith, who mainly create iron_pickaxe.
# """


class RoleAgent:
    def __init__(self, llm):
        self.llm = llm

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

    def make_todaysgoal(self, dream, inventory, memory):
        print("~~~~~~~~~~make_todaysgoal~~~~~~~~~~~")
        system_prompt = """
        You are an assistant of the role playing of Minecraft game.
        We regard completing role as getting item set as goal.
        Your task is translating given role texts into item list(python-dict-type) as a goal.
        Please answer the item list that a player who is given the role will finaly get.
        Each time, I give you information below:
        Role: ... ;This is the role which player will be given.
        Invenotory: {{"ITEM_NAME":COUNT,...}} : Those are items which player has now.
        Memory: [{{"TASK":COUNT}},...] ;Those are the tasks you achieved before.

        Here are what you have to pay attention to.
        While you are answering, please use correct item name of minecraft. do not use ambiguous name like "fertilizer, animal, food, tool, material".
        you only have to answer the result. please do not answer other text.
        You must follow the python-dict like format below when you answer:
        {{"ITEM_NAME":COUNT}}

        Here is an example:
        {{"diamond_sword":3}}
        """
        human_prompt = f"Role: {dream} Inventory: {inventory} Memory: {memory}, what does the player have to get to complete role playing? "
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="recipe")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        # print(extracted_response)
        return extracted_response
    
    def next_task(self, role, todaysgoal, inventory, memory=None):
        print("~~~~~~~~~~next task~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Role: {role} Inventory: {inventory} Memory: {memory} What is the next task?"
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="action")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        # print(extracted_response)
        return extracted_response
    

        
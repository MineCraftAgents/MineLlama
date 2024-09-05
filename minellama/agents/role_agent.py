import re
import json
from pathlib import Path

#このファイルはtodoを細かく分解して進めていく方式のもの

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

    def extract_list_from_str(self,response):
        matched = re.search(r'(\[.*?\])', response, re.DOTALL)
        if matched:
            json_list = matched.group(1).strip()
            # print("json_list: ",json_list)
            return json.loads(json_list)
        else:
            print("No list found. Trying again.")
            return None

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

    def make_todaysgoal(self, dream, inventory, memory, error_message="none", max_iterations=10):
        print("~~~~~~~~~~make_todaysgoal~~~~~~~~~~~")
        system_prompt_todo = """
        You are assisting with role-playing in the Minecraft game.

        Your task is to translate the given role text into a TO-DO list for today (in Python list format) that represents the goal.

        Each time, you will be given:

        Role: This is the role the player has been assigned.
        Inventory: {{"ITEM_NAME":COUNT,...}} — These are the items the player currently has.
        Memory: [{{"TASK":COUNT}},...] — These are the tasks you have completed before.
        Error_Message: This is the error message fromt the last round.

        Your goal is to determine and output a TO-DO list for today that the player should have to complete the given role. The output should be in the following format:
        ["Action1", "Action2",...]

        However, the actions you can do in this Minecraft game are limitied. Here are the possible actions:
        Collect, craft, plant, harvest, fish, kill, smelt.

        Please follow these instructions:

        1.Use accurate Minecraft item names, and avoid ambiguous terms such as fertilizer, animal, food, tool or material.
        2.Provide your answers in the format of a Python list.
        3.Clarify the action for each TO-DO. For example, "Collect log", "Craft stone_sword", or "Harvest wheat".
        4.The TO-DO list is only for today. Don't make too much.
        4.Only provide the answer in the specified format and do not include additional explanations or comments.
        """
        
        iterations = 0
        while iterations < max_iterations:
            human_prompt_todo = f"Role: {dream} Inventory: {inventory} Memory: {memory} Error_message: {error_message}, what does the player have to do today to complete role playing? "
            print(human_prompt_todo)
            response = self.llm.content(system_prompt_todo, query_str=human_prompt_todo, data_dir="recipe")
            print("response:",response)
            extracted_response = self.extract_list_from_str(response)
            if extracted_response is not None:
                return extracted_response
            else:
                error_message = "Invalid Error. No list found."
        
        # checked = []
        # i = 0
        # for item in extracted_response:
        #     print(item)
        #     if self.check_item_name(extracted_response[item]):
        #         print(f"{item} is a correct minecraft item name")
        #         checked.append(extracted_response[i])
        #     i = i + 1
        
        # print("checked response : ", checked)
        # print(extracted_response)
        # return checked
        return extracted_response
    
    def make_todo_detail(self, dream, todo, inventory, memory, max_iterations=10):
        print("~~~~~~~~~~~todo detail~~~~~~~~~~")
        system_prompt_todo_detail = """
        You are providing support for Minecraft gameplay. Your task is to output the actions the player should take in Minecraft based on the given short sentences according to the instructions below. The output should be a list with elements of type Python dict. Each dict should have the format:
        [{{"action": action name, "item_name": name of the item, "count": number of items}}]
        Each time, you will be given:
        To Do: The general goal the player wants to achieve.
        Inventory: {{"ITEM_NAME": COUNT, ...}} — These are the items the player currently has.
        Memory: [{{"TASK": COUNT}}, ...] — These are the tasks you have completed before.
        Error_Message: This is the error message fromt the last round.

        What you can do is here. You must choose one of these actions when you choose "action".
        1) craft :Use this to craft item. 
        2) smelt:Use this to smelt item.
        3) mine:Use this to mine block. 
        4) collect:Use this to collect item.
        5) kill:Use this to get item by killing entities. 
        6) fish:Use this to catch fish.
        7) tillAndPlant :Use this to plant seeds. You need seeds and hoe first. You will find and go to water, till  farmland with hoe, and plant seeds with this function.
        8) harvest:Use this to harvest wheat. You have to plant seeds first. You will wait for wheat around you to grow and harvest them with this.

        Please follow these guidelines when creating your output:
        1. Use item names that exist within Minecraft. For example: stone_pickaxe.
        2. The output should be in the format of a Python list. Each element should be a dict in the previously mentioned format: [{{"action": action name, "item_name": name of the item, "count": number of items}}]. For example: `[{{"action": action name, "item_name": name of the item, "count": number of items}}].
        3. For action name, choose from ["craft", "mine", "smelt", "collect", "kill", "fish", "tillAndPlant", "harvest"]. Do not use any other names.
        4. Do not output answers that are not listed above. No additional explanations or clarifications are needed.
        5. Under no circumstances should there be any line breaks.
        """
        #[{{"action": "mine", "item_name": "cobblestone", "count": 3}}, {{"action": "craft", "item_name": "stick", "count": 2}}, {{"action": "craft", "item_name": "stone_pickaxe", "count": 1}}]
        #Dream : Your role. you have to fullfill this order.
        
        #Dream:{dream}, 
        iterations = 0
        error_message = ""
        while iterations < max_iterations:
            human_prompt_todo_detail = f"To Do: {todo}, Inventory: {inventory} Memory: {memory}, error messagae:{error_message}, what does the player have to do today? "
            # print(human_prompt_todo_detail)
            try :
                response = self.llm.content(system_prompt_todo_detail, query_str=human_prompt_todo_detail, data_dir="recipe")
                print("response:",response)
                extracted_response = self.extract_list_from_str(response)
            except Exception as e:
            # 予期しないエラーをキャッチする
                print(f"Unexpected error occurred. Moving to the next iteration.")
                continue
            if extracted_response is not None:
                func_list=["craft", "mine", "smelt", "collect", "kill", "fish", "tillAndPlant", "harvest"]
                done = 0
                for item in extracted_response:
                    if item['action'] not in func_list:
                        error_message += f"There is no action called {item['action']}.\n"
                        done += 1 
                if done == 0:
                    return extracted_response
                error_message += f'This is your response from last round: {extracted_response}'
                print(f'This is your response from last round: {extracted_response}')
            else:
                error_message += "Invalid Error. No list found."
                print("Invalid Error. No list found.")
            
    
    
    #todo_detailを作成する場合、next_taskは役割がかぶるので不要になる？    
    def next_task(self, role, todaysgoal, inventory, memory=None):
        print("~~~~~~~~~~next task~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Today's goal: {todaysgoal} Inventory: {inventory} Memory: {memory} What is the next task?"
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="action")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        # print(extracted_response)
        return extracted_response
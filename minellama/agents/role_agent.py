import re
import json
from pathlib import Path

#このファイルはtodoを細かく分解して進めていく方式のもの

# role_explanation = """
# You are a smith, who mainly create iron_pickaxe.
# """


class RoleAgent:
    def __init__(self, llm, func_list):
        self.llm = llm
        self.func_list = func_list

        data_path = ""
        data_path = str(Path(__file__).parent / data_path)
        with open(f"{data_path}/minecraft_dataset/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}
        with open(f"{data_path}/minecraft_dataset/entities.json", "r") as f:
            entities_json = json.load(f)
            self.mc_entities = {item['name']: item for item in entities_json}


    def extract_list_from_str(self,response):
        matched = re.search(r'(\[.*?\])', response, re.DOTALL)
        if matched:
            json_list = matched.group(1).strip()
            # print("json_list: ",json_list)
            return json.loads(json_list)
        else:
            print("No list found. Trying again.")
            return None

    def check_invalid_name(self, name:str):
        if name in self.mc_items or name in self.mc_entities:
            return False
        else :
            return True

    def make_todaysgoal(self, dream, inventory, biome, nearby_block, nearby_entities, memory, max_iterations=10):
        system_prompt = """
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
        5.Only provide the answer in the specified format and do not include additional explanations or comments.
        6.The length of output-list should be 1 or 2.
        """
        
        iterations = 0
        error_message = ""
        while iterations < max_iterations:
            print("Generating Today's Goal...")
            query_str = f"Role: {dream} Inventory: {inventory} Biome: {biome} Nearby Block: {nearby_block} Nearby Entities: {nearby_entities} Memory: {memory} Error_message: {error_message},  what does the player have to do today to complete role playing? "
            human_prompt = ""
            try :
                response = self.llm.content(system_prompt=system_prompt, human_prompt=human_prompt, query_str=query_str, data_dir="recipe")
                # print("response:",response)
                extracted_response = self.extract_list_from_str(response)
                if extracted_response is not None:
                    if len(extracted_response) > 0:
                        print(response)
                        return extracted_response
                else:
                    error_message = "Invalid Error. No list found."
            except Exception as e :
                print("Unexpected error was occured. Trying again ...")
                print(e)
                continue
        
        return extracted_response
    
    def make_todo_detail(self, dream, todo, inventory, biome, nearby_block, nearby_entities, memory, max_iterations=10):
        system_prompt = """
        You are providing support for Minecraft gameplay. Your task is to output the actions the player should take in Minecraft based on the given short sentences according to the instructions below. The output should be a list with elements of type Python dict. Each dict should have the format:
        [{{"action": action name, "name": name of the item or entity, "count": number of items}}]
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
        5) kill:Use this to kill entity. This includes collecting dropped items.
        6) fish:Use this to catch fish.
        7) tillAndPlant :Use this to plant seeds. You need seeds and hoe first. You will find and go to water, till  farmland with hoe, and plant seeds with this function.
        8) harvest:Use this to harvest wheat. You have to plant seeds first. You will wait for wheat around you to grow and harvest them with this.

        Please follow these guidelines when creating your output:
        1. Use item names that exist within Minecraft. For example: stone_pickaxe.
        2. The output should be in the format of a Python list. Each element should be a dict in the previously mentioned format: [{{"action": action name, "name": name of the item or entity, "count": number of items}}]. For example: `[{{"action": "mine", "name": "cobblestone", "count": 3}}].
        3. For action name, choose from ["craft", "mine", "smelt", "collect", "kill", "fish", "tillAndPlant", "harvest"]. Do not use any other names.
        4. Do not output answers that are not listed above. No additional explanations or clarifications are needed.
        5. Under no circumstances should there be any line breaks.
        5.The length of output-list should be 1 or 2.
        """
                
        print("Generating TODO details...")
        iterations = 0
        error_message = ""
        while iterations < max_iterations:
            query_str = f"To Do: {todo}, Inventory: {inventory}, Nearby block: {nearby_block}, Nearby entities: {nearby_entities}, Dream: {dream}, Memory: {memory}, error message:{error_message}, what does the player have to do today? "
            human_prompt = ""
            error_message = ""
            try :
                response = self.llm.content(system_prompt=system_prompt, human_prompt=human_prompt, query_str=query_str, data_dir="result")
                extracted_response = self.extract_list_from_str(response)
            except Exception as e:
            # 予期しないエラーをキャッチする
                print(f"Unexpected error occurred. Moving to the next iteration.\n{e}")
                continue
            if extracted_response is not None:
                done = True
                for item in extracted_response:
                    try:
                        if item['action'] not in self.func_list:
                            error_message += f"There is no action called {item['action']}.\n"
                            print(f"\nThere is no action called {item['action']}.\n")
                            done = False
                        if self.check_invalid_name(item['name']):
                            error_message += f"There is no item or entities called {item['name']}.\n"
                            print(f"\nThere is no item or entities called {item['name']}.\n")
                            done = False
                    except Exception as e:
                        error_message += f'Format was invaild. Please use the format [{{"action": action name, "name": name of the item or entity, "count": number of items}}]\n'
                        print(f"\nFormat was invalid.\n")
                        done = False
                if done:
                    print(response)
                    return extracted_response
                #error_message += f'This is your response from last round: {extracted_response}\n'
                print(f'This is your response from last round: {extracted_response}\n')
            else:
                error_message += f"Invalid Error. No list found.\n"
                print(f"\nInvalid Error. No list found.\n")
        
        #LLMの出力が不安定なので、本当に一度も有効な回答が手に入らなかった場合の緊急措置。どのタスクにも要求されるアイテムを補充する。        
        instant_task = [{"action": "craft", "name": "crafting_table", "count": 1}, {"action": "mine", "name": "log", "count": 5}, {"action": "mine", "name": "cobblestone", "count": 5}]
        return instant_task
    
    
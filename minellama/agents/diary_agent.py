import re
import json

#wikiを参照ない場合

class DiaryAgent:
    def __init__(self, llm):
        self.llm = llm

    def extract_dict_from_str(self, response: str) -> dict:
        matched = re.search(r'(\{.*\})', response)
        if matched:
            json_dict = matched.group(1).strip()
            extracted_dict = json.loads(json_dict.replace("'", '"'))
            
            if 'result' in extracted_dict:
                return extracted_dict["result"]
            else:
                print("The key 'json' is not found in the extracted dictionary.")
                raise KeyError("Missing 'json' key in the extracted dictionary")
        else:
            print("No JSON dictionary found. Trying again.")
            raise Exception("Invalid Format Error")

    def summarize_inventory(self, final_inventory, initial_inventory):
        summary = []
        all_items = set(initial_inventory.keys()).union(final_inventory.keys())
        
        for item in all_items:
            initial_count = initial_inventory.get(item, 0)
            final_count = final_inventory.get(item, 0)
            
            if final_count > initial_count:
                summary.append(f"I got {final_count - initial_count} {item}.")
            elif final_count < initial_count:
                summary.append(f"I lost {initial_count - final_count} {item}.")
            else:
                summary.append(f"I still have {initial_count} {item}.")
        
        return "\n".join(summary)

    def evaluate_result(self, task:dict, final_inventory:dict, initial_inventory:dict, nearby_block:list=[], chat_log:str="", error:str="", max_iterations=10):
        system_prompt = """
        You are a helpful assistant of Minecraft game.
        I will give you the task to be completed in Minecraft game, and I want you to evaluate the result wheather I completed the task or failed, with the information I provide.

        The information below will be provided each time:
        Task:.. // This is the task to complete in the game.
        Inventory diff:.. // This is information regarding the increase and decrease of items in the inventory.
        Nearby block:.. // This is information regarding the blocks nearby.
        Chat log:.. // This is chat log in Minecraft. This is useful since it's feedbacks from the game. It includes error info as well.
        Error:.. // If there is an error, the task is probably failed.

        The following are output instructions. Please follow them strictly:
        1. The evaluation result must be 1 sentence. It should be short and clear. For example: 'I completed crafting 3 planks.', 'I failed killing 2 sheep.'
        2. The evaluation result has to be JSON format, e.g. {{"result":'I completed harvesting 4 wheat.'}}
        3. I want your explanation of the evaluation.

        Here are some examples:
        Task: kill 3 spiders
        Inventory_diff: I got 2 cobblestone. I got 3 string. I lost 1 wooden_sword.

        You would answer:
        {{"result":"I completed killing 3 spiders"}}
        Explanation: 
        Since you got 3 string in your inventory, it seems that you succeeded the task.

        Task: tillAndPlant 2 wheat_seeds
        Inventory: I lost 1 wheat_seeds.
        Nearby Block: ["farmland", "dirt"]
        Chat log: Succeeded tilling dirt. Failed planting wheat_seed.
        You would answer:
        {{"result":"I failed tillAndPlant 2 wheat_seeds"}}
        Explanation: 
        Since you lost only 1 wheat_seeds, it seems that you only planted 1 seed, which means you failed planting 2 seeds.
        """
        iterations = 0
        while iterations < max_iterations:
            task_txt = f"{task['action']} {task['count']} {task['item_name']}"
            inventory_txt = self.summarize_inventory(final_inventory=final_inventory, initial_inventory=initial_inventory)
            query = f"Task:{task_txt} \nInventory diff:{inventory_txt} \nNearby block:{nearby_block} \nChat log:{chat_log} \nError: {error}"
            try:
                response = self.llm.content(system_prompt, query_str=query, data_dir="result")
                print(response)
                result = self.extract_dict_from_str(response=response)
                return result
            except Exception as e:
                print(e)
                iterations += 1


    def generate_diary(self, initial, final, tasks, numofday):
        print("~~~~~~~~~~generate_diary~~~~~~~~~~~~")
        system_prompt = """
        You are providing support for Minecraft gameplay. As part of this activity, you need to create a simple diary summarizing which tasks were successful or failed by using the inventory status at the beginning and end of the day, as well as the list of tasks assigned for that day.

        The information provided each time is as follows:
        num_of_day: int //The number of the day.
        initial_inventory:[{{"ITEM_NAME":"COUNT"}}, …]   //The list of items you had at the beginning of the day.
        final_inventory:[{{"ITEM_NAME":"COUNT"}}, …]   //The list of items you had at the end of the day after completing the tasks.
        tasks:[{{"action": action name, "item_name": name of the item, "count": number of items}}, …]   //The list of tasks you were supposed to complete that day.

        For example, if you receive the following information:
        num_of_day : 4
        initial_inventory:[{{"stick":2}}, …]  
        final_inventory:[{{"stick":"2"}}, {{"cobblestone":1}}, {{"wooden_pickaxe":1}}]
        tasks:[{{"action": "mine", "item_name": "cobblestone", "count": 3}}, {{"action": "craft", "item_name": "wooden_pickaxe", "count": 1}}, {{"action": "harvest", "item_name": "wheat", "count": 3}}]  
        You would create a diary entry as follows:
        - Since only one cobblestone was gained from the initial_inventory to the final_inventory, and the task was to mine 3 cobblestone, it means "failed to mine 3 cobblestone."
        - Next, since a wooden_pickaxe was gained and the original task was to craft 1 wooden_pickaxe, it means "succeeded in crafting 1 wooden_pickaxe."
        - Finally, since wheat is not present in either the initial_inventory or the final_inventory, it means "failed to harvest 3 wheat."

        Thus, the final diary entry would be:
        "DIARY": Day 4, I failed to mine 3 cobblestone, succeeded in crafting 1 wooden_pickaxe, and failed to harvest 3 wheat.

        The following are output instructions. Please follow them strictly:
        1: Only output the "DIARY" part from the example above, that is, the complete diary entry. Do not output anything else.
        2: Use Minecraft in-game terminology for output. Do not use any other words.
        3: Clearly indicate which tasks were successful or failed.

        """
        human_prompt = f"num_of_day:{numofday}, initial_inventory: {initial} , final_inventory: {final}, tasks:{tasks} Using this information, please create the diary."
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="result", similarity_top_k = 7)
        #print(response)
        return response
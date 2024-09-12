import re
import json

#wikiを参照ない場合

class DiaryAgent:
    def __init__(self, llm):
        self.llm = llm

        self.diary_prompt = """
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


    def generate_diary(self, initial, final, tasks, numofday):
        print("~~~~~~~~~~generate_diary~~~~~~~~~~~~")
        system_prompt = self.diary_prompt
        human_prompt = f"num_of_day:{numofday}, initial_inventory: {initial} , final_inventory: {final}, tasks:{tasks} Using this information, please create the diary."
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="result", similarity_top_k = 7)
        #print(response)
        return response
import re
import json

#wikiを参照ない場合

class DreamAgent:
    def __init__(self, llm):
        self.llm = llm

    def generate_dream(self, role, numofDate, lastDream, inventory, memory=None):
        system_prompt = """
        You are assisting with Minecraft roleplay. 
        If assigned a role, describe in one specific and concise sentence whether similar actions should be taken.
        
        Each time, you will be given:
        Role:This is the role name that a player want to play.
        Memory: [{{"TASK":COUNT}},...] ;Those are the tasks you achieved before. 

        Be sure to follow these instructions:
        1. Write the answer in simple sentences. Do not make it long.
        2. Output only the answer, without any additional text.
        3. Use only Minecraft item names in your answer. Do not use any other names.
        """
        #human_prompt = f"Role: {role} Memory: {memory} Using this information, provide a Minecraft-based description for the role."
        print("Generating Dream...")
        if numofDate == 1:
            query_str = f"Today is the first day. What should you start doing in the Minecraft game to achieve the Role:{role}?"
        else :
            query_str = f"Today is the {numofDate}-th day. Yesterday, I received instructions from you with the content Operation:{lastDream}, and I carried it out. Now, my inventory is {inventory}. What tasks should I continue to work on to achieve the Role:{role}? Here is a detailed record of yesterday's work. Please refer to it. Memory:{memory}"
        response = self.llm.content(system_prompt=system_prompt, query_str=query_str, data_dir="recipe")
        #print(response)
        return response
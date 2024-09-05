import re
import json

#wikiを参照ない場合

class DreamAgent:
    def __init__(self, llm):
        self.llm = llm

        self.role_prompt = """
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


    def generate_dream(self, role, memory=None):
        print("~~~~~~~~~~generate_dream~~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Role: {role} Memory: {memory} Using this information, provide a Minecraft-based description for the role."
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="recipe")
        print(response)
        return response
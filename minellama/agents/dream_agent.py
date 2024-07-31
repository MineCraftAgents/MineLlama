import re
import json

class DreamAgent:
    def __init__(self, llm):
        self.llm = llm

        self.role_prompt = """
        You are playing a role in Minecraft game.
        I want you to translate Wikipedia's general description of Minecraft to a description based on item names and concepts and tasks you have done in the past. 
        Each time, I give you information below:
        Wikipedia: ... ;This is a wikipedia description of Role in general.
        Memory: [{{"TASK":COUNT}},...] ;Those are the tasks you achieved before. 
        
        You must follow the python-dict like format below when you answer:
        {{"Minecraft-based Description":TEXT}}

        Here is an example:
        {{"Minecraft-based Description":"To be a farmer, I should plant many vegetables or plant."}}
        """


    def generate_dream(self, role, memory=None):
        print("~~~~~~~~~~generate_dream~~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Wikipedia: {role} Memory: {memory} Using this information, provide a Minecraft-based description for the role."
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="dream")
        print(response)
        return response


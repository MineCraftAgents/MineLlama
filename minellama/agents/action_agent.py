import re
import json 
from pathlib import Path

class ActionAgent:
    def __init__(self, llm):
        self.llm=llm
        self.memory = {}
        data_path = str(Path(__file__).parent / "minecraft_dataset")
        with open(f"{data_path}/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}
        with open(f"{data_path}/entities.json", "r") as f:
            entities_json = json.load(f)
            self.mc_entities = {item['name']: item for item in entities_json}

    def save_action(self, subgoal, code):
        self.memory[str(subgoal)] = code
        print(f"Saved new code: {self.memory}\n")
        return
    
    def reset(self):
        self.memory = {}

    def extract_jscode(self, response = ""):
        js_code_match = re.search(r'(await.*?;)', response, re.DOTALL)
        if js_code_match:
            js_code = js_code_match.group(1).strip()
            print("============= Code Extraction Success ============= \n",js_code)
            return js_code
        else:
            error = "No JavaScript code found after 'YOUR ANSWER'. Trying again.\n"
            raise Exception(error)
        
    
    def check_name(self, code = ""):
        match = re.search(r'\((.*?)\)', code)
        if match:
            inside_parentheses = match.group(1)
            elements = [elem.strip() for elem in inside_parentheses.split(',')]
            if len(elements) > 1:
                second_value = elements[1]
                # アイテム名が ' または " で囲まれている場合、囲みを削除
                if (second_value.startswith("'") and second_value.endswith("'")) or (second_value.startswith('"') and second_value.endswith('"')):
                    name = second_value[1:-1]
                    if name in self.mc_items or name in self.mc_entities:
                        print("Validated item name:", name)
                        return 
                    else:
                        error = f"There is no item or entity called {name} in Minecraft.\n"
                        raise Exception(error)
            error = "No second value found after bot\n"
            raise Exception(error)
        else:
            error = "No parentheses found\n"
            raise Exception(error)
    

    def generate_action(self, task="", context="", nearby_block=[], nearby_entities=[], last_code="", error_message="", chat_log="", data_dir="action", max_iterations=10):
        iterations = 0
        system_prompt = '''
You are a helpful assistant of Minecraft game.
I want you to choose one function to achive the task.

Here are some javascript functions:
1) craft(bot, item_to_craft, count); //Use this to craft item.
2) smelt(bot, item_to_smelt, count, fuel); //Use this to smelt item. fuel should be 'planks'.
3) mine(bot, block_to_mine, count, tool); //Use this to mine block. When you need tools to mine, give it as an argument, e.g. 'wooden_pickaxe' to mine stone.
4) kill(bot, entity_to_kill, count, tool); //Use this to get item by killing entities. When you need tools to kill, give it as an argument, e.g. 'wooden_sword'.
5) fish(bot, count); //Use this to catch fish.
6) tillAndPlant(bot, seedName, count, hoeName); //Use this to plant seeds. You need seeds and hoe first. You will find and go to water, till  farmland with hoe, and plant seeds with this function.
7) harvest(bot, name, count); //Use this to harvest wheat. You have to plant seeds first. You will wait for wheat around you to grow and harvest them with this.


I will give you the following information for each time:
Task: {{"name":count}}
Nearby Block: ["block1", "block2",...] //This could be useful when you mine block.
Nearby Entities: ["entity1", "entity2",...] //This could be useful when you kill entity to get item.
Context: ... //This is about how to achieve the task. You should refer to this to decide which action to choose.
Code from the last round: ... //This is the code from the last round.
Error Message: ... //This is error messages from the last round.
Chat Log: ... //This is chat log from the last round. This is feedback from Minecraft game.

Please note that
1) The arguments item should be string and count should be number, and the first argument must be bot.
2) You have to call only one function with starting 'await', e.g. await craft(bot, 'stone_pickaxe',1);
3) Please use underscores _ instead of spaces for the names and tools, e.g. not 'crafting table' but 'crafting_table'
4) Be careful with the argument 'count', put the correct number in it. Please pay attention to Task dict, which indicates 'count' as the argument.
5) Context is helpful. You shoud choose the correct function with arguments considering both context and nearby block or entities. Don't put the ingredient as the argument. You don't need to care the ingredients. Follow the format above and put the arguments carefully. 

Here are some examples:
Example 1)
Task: {{"cobblestone":3}}
Nearby Block: ["stone", "dirt", "oak_log"]
Context: You can get cobblestone by breaking stone. You need wooden_pickaxe to break it. You can get cobblestone by breaking cobblestone. You need wooden_pickaxe to break it.
Then, you would answer:
await mine(bot, 'stone', 3, 'wooden_pickaxe');

Example 2)
Task: {{"beef":2}}
Nearby Entities: ["cow", "pig"]
Context: You can get beef by killing cow.
Then, you would answer:
await kill(bot, 'cow', 2);

Example 3)
Task: {{"iron_sword":1}}
Context: You alreaday have all ingredients and tools. Please craft or smelt {{'iron_sword': 1}}.
You can get iron_sword by crafting with crafting_table.
Then, you would answer:
await craft(bot, 'iron_sword',1);

Example 4)
Task: {{"iron_ingot":2}}
Context: You can get iron_ingot by smelting raw_iron with furnace.
Then, you would answer:
await smelt(bot, 'raw_iron', 2, 'planks');

'''
        print("\nGenerating action by action agent...")
        while iterations < max_iterations:
            try:
                human_prompt = f"Choose the function with the arguments to achive the task below please.\nTask : {task}\nNearby Block : {nearby_block}\nNearby Entities : {nearby_entities}\nContext : {context}\nCode from the last round: {last_code}\nError Message: {error_message}\nChat Log: {chat_log}"
                output = self.llm.content(system_prompt=system_prompt,query_str=human_prompt, data_dir=data_dir)
                code = self.extract_jscode(response = output)
                self.check_name(code=code)
                return code
            except Exception as e:
                print(e)
                error_message = e
                iterations += 1
                continue

        print("You reached the max iterations.")
        return 
    
    def get_action(self, goal, context="", nearby_block=[], nearby_entities=[], last_code="", error_massage="", chat_log="", retrieval=True):
        # 過去に成功したアクションを使い回す。
        if retrieval:
            if str(goal) in self.memory:
                code = self.memory[str(goal)]
                print(f"\nRetrieved code from memory:  {code}\n")
                return code
        # context = self.llm.get_context(task=goal)
        code = self.generate_action(task=goal,context=context, nearby_block=nearby_block, nearby_entities=nearby_entities, last_code=last_code, error_message=error_massage, chat_log=chat_log, data_dir="action")
        return code
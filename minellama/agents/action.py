import re

class ActionGenerator:
    def __init__(self, llm):
        self.llm=llm

    def extract_jscode(self, response = ""):
        js_code_match = re.search(r'(await.*?;)', response, re.DOTALL)
        if js_code_match:
            js_code = js_code_match.group(1).strip()
            print("============= Code Extraction Success ============= \n",js_code)
            return js_code
        else:
            print("No JavaScript code found after 'YOUR ANSWER'. Trying again.")
            return None
    

    def generate_action(self, task="", context="", error_message="", index_dir="context", max_iterations=10):
        iterations = 0
        system_prompt = '''
You are a helpful assistant of Minecraft game.
I want you to choose one function to achive the task.

Here are some javascript function:
1) craft(bot, item, count); //Use this to craft item. 
2) smelt(bot, item, count, fuel); //Use this to smelt item. fuel should be 'planks'.
3) mine(bot, item, count, tool); //Use this to mine item. When you need tools to mine, give it as an argument, e.g. 'wooden_pickaxe' to mine stone.
4) kill(bot, entity, count, tool); //Use this to get item by killing entities. When you need tools to kill, give it as an argument, e.g. 'wooden_sword'.

I will give you the following information for each time:
Task: {{"name":count}}

Please note that
1) The arguments item should be string and count should be number, and the first argument must be bot.
2) You have to call only one function with 'await', e.g. await craft(bot, 'stone_pickaxe',1);
3) Please use underscores _ instead of spaces for the names and tools, e.g. not 'crafting table' but 'crafting_table'
4) Be careful with the argument 'count', put the correct number in it. Please pay attention to Task dict, which indicates 'count' as the argument.
5) Context might be wrong. Don't rely too much on it. Don't put the ingredients as the argument. You don't need to care the ingredients. Follow the format above and put the arguments carefully. 

Here are some examples:
Example 1)
Task: {{"cobblestone":3}}
Context: You need wooden_pickaxe to mine cobblestone.
Then, you would answer:
await mine(bot, 'cobblestone', 3, 'wooden_pickaxe');

Example 2)
Task: {{"beef":2}}
Context: You have to kill a cow to get beef.
Then, you would answer:
await kill(bot, 'cow', 2);

Example 3)
Task: {{"iron_sword":1}}
Context: You have to craft it with crafting table.
Then, you would answer:
await craft(bot, 'iron_sword',1);

Example 4)
Task: {{"iron_ingot":2}}
Context: You have to smelt raw_iron to get iron_ingot.
Then, you would answer:
await smelt(bot, 'raw_iron', 2, 'planks');


'''
        human_prompt = f'''
Choose the function with the arguments to achive the task below please.
Task : {task}
'''

        while iterations < max_iterations:
            output = self.llm.content(system_prompt=system_prompt,query_str=human_prompt, index_dir=index_dir)
            print(output)
            code = self.extract_jscode(response = output)
            if code is not None:
                return code
            iterations += 1
            print("Current iterations: ", iterations)

        print("You reached tha max iterations.")
        return 
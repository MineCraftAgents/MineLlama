import copy
import json
import os
import time
from typing import Dict
from datetime import datetime

import minellama.utils as U
from .env import VoyagerEnv

from .agents import RoleAgent, DreamAgent, RecipeAgent, ActionAgent, DiaryAgent
from .llm import Llama2,GPT
from .control_primitives import load_control_primitives

class Minellama:
    def __init__(
        self,
        mc_port: int = None, # Minecraft port
        server_port: int = 3000,
        openai_api_key: str = None, # OpenAI API Key
        env_wait_ticks: int = 20,
        env_request_timeout: int = 6000,
        max_iterations: int = 10, # Max iterations for each task. If reached it, it skips the task to the next.
        difficulty: str = "peaceful", # Difficulty of Minecraft game
        llm: str = None, # "llama" or "gpt"
        llm_model: str = None, # "meta-llama/Llama-2-70b-chat-hf" for Llama2, "gpt-3.5-turbo" or "gpt-4" for GPT
        local_llm_path: str = None, # If you have local Llama2, set the path to the directory. If None, it will create the model dir in minellama/llm/ .
        hf_auth_token: str = "", # Hugging face auth token.
        record_file: str = "./log.txt", # the output file to record the result.
    ):
        # init env
        self.env = VoyagerEnv(
            mc_port=mc_port,
            server_port=server_port,
            request_timeout=env_request_timeout,
        )
        self.env_wait_ticks = env_wait_ticks
        self.max_iterations_rollout = max_iterations

        # set LLM
        if llm == "llama":
            print("Llama2 called")
            self.llm = Llama2(hf_auth_token=hf_auth_token, llm_model=llm_model, local_llm_path=local_llm_path)
        elif llm == "gpt":
            print("GPT called")
            os.environ["OPENAI_API_KEY"] = openai_api_key
            self.llm = GPT(llm_model=llm_model)
        else:
            # This is for baseline without LLM
            raise ValueError("No LLM selected.")
            

        self.recipe_agent = RecipeAgent(llm=self.llm)
        self.action_agent = ActionAgent(llm=self.llm)
        self.role_agent = RoleAgent(llm=self.llm)
        self.dream_agent = DreamAgent(llm=self.llm)
        self.diary_agent = DiaryAgent(llm=self.llm)

        self.control_primitives = load_control_primitives()

        # Minellama info
        self.inventory_rawdata = {}
        self.inventory = {} # processed inventory for log and planks
        self.initial_inventory = {}
        self.final_inventory = {}
        self.nearby_block = []
        self.equipment = []
        self.biome = ""
        self.nearby_entities = []
        self.time_of_day = ""
        self.health = 20
        self.hunger = 20
        self.chat_log = ""
        self.error = ""

        self.last_code = ""
        self.last_context = ""
        self.action_agent_rollout_num_iter = -1
        self.last_events = None

        self.role = None
        self.dream = ""
        self.todaysgoal = ""
        self.num_of_date = 1
        self.memory = []
        self.diary_txt = ""
        self.daily_executed_tasks = []
        self.todo_detail = {}

        self.success_list = []
        self.failed_list = []
        self.difficulty = difficulty
        self.task_list = []
        self.next_task = {}
        self.subgoal_memory = []
        self.subgoal_memory_success = []
        self.subgoal_memory_failed = []
        self.step_count = 0

        self.record_file = record_file 
        with open(self.record_file, "a") as f:
            formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n=========== The record at {formatted_datetime} ============\n")

    def programs(self):
        programs = ""
        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"
        return programs
    
    def record_log(self, success=False, todo=""):
        with open(self.record_file, "a") as f:
            text = f"\n\nNUM_OF_DATE: {self.num_of_date}"
            text += f"Role: {self.role}\n"
            text += f"DREAM: {self.dream}\n"
            text += f"SELECTING_TO_DO: {todo}"
            text += f"TASK: {self.next_task}\n"
            text += f"SUCCESS: {success}\n"
            text += f"INVENTORY: {self.inventory}\n"
            text += f"SUBGOAL_MEMORY: {self.subgoal_memory}\n"
            text += f"SUBGOAL_SUCCESS: {self.subgoal_memory_success}\n"
            text += f"SUBGOAL_FAILED: {self.subgoal_memory_failed}\n"
            text += f"ACTION_MEMORY: {self.action_agent.memory}\n"
            text += f"LAST_ERROR_MASSAGE: {self.error}\n"
            text += f"LAST_CHAT_LOG: {self.chat_log}\n"
            text += f"LAST_CODE_AND_CONTEXT: {self.last_code}\n{self.last_context}\n"
            text += f"RECIPE_PATHS:\n{self.recipe_agent.paths}\n"
            text += f"STEP_COUNT: {self.step_count}\n"
            text += f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f.write(text)  

    def process_inventory(self, inventory_rawdata:dict):
        log_list = ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log"]
        planks_list = ["oak_planks", "birch_planks", "spruce_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "mangrove_planks"]
        inventory = copy.deepcopy(inventory_rawdata)
        inventory_keys = list(inventory.keys())
        log_count = 0
        planks_count = 0
        for key in inventory_keys:
            if key in log_list:
                log_count += inventory[key]
                inventory.pop(key)
            elif key in planks_list:
                planks_count += inventory[key]
                inventory.pop(key)

        if log_count > 0 :
            inventory["log"] = log_count
        if planks_count > 0 :
            inventory["planks"] = planks_count
            
        return inventory

    def interpret_events(
        self, *, events, code="", task="", subgoal="", context="", critique=""
    ):
        chat_messages = []
        error_messages = []
        # FIXME: damage_messages is not used
        damage_messages = []
        assert events[-1][0] == "observe", "Last event must be observe"
        for i, (event_type, event) in enumerate(events):
            if event_type == "onChat":
                chat_messages.append(event["onChat"])
            elif event_type == "onError":
                error_messages.append(event["onError"])
            elif event_type == "onDamage":
                damage_messages.append(event["onDamage"])
            elif event_type == "observe":
                biome = event["status"]["biome"]
                time_of_day = event["status"]["timeOfDay"]
                voxels = event["voxels"]
                entities = event["status"]["entities"]
                health = event["status"]["health"]
                hunger = event["status"]["food"]
                position = event["status"]["position"]
                equipment = event["status"]["equipment"]
                inventory_used = event["status"]["inventoryUsed"]
                inventory = event["inventory"]
                assert i == len(events) - 1, "observe must be the last event"

        observation = ""

        if code:
            observation += f"Code from the last round:\n{code}\n\n"
        else:
            observation += f"Code from the last round: No code in the first round\n\n"

        if error_messages:
            error = "\n".join(error_messages)
            observation += f"Execution error:\n{error}\n\n"
            self.error = error
        else:
            observation += f"Execution error: No error\n\n"
            self.error = ""

        if chat_messages:
            chat_log = "\n".join(chat_messages)
            observation += f"Chat log: {chat_log}\n\n"
            self.chat_log = chat_log
        else:
            observation += f"Chat log: None\n\n"
            self.chat_log = ""

        observation += f"Biome: {biome}\n\n"
        self.biome = biome

        observation += f"Time: {time_of_day}\n\n"
        self.time_of_day = time_of_day

        if voxels:
            observation += f"Nearby blocks: {', '.join(voxels)}\n\n"
            self.nearby_block = voxels
        else:
            observation += f"Nearby blocks: None\n\n"

        if entities:
            nearby_entities = [
                k for k, v in sorted(entities.items(), key=lambda x: x[1])
            ]
            observation += f"Nearby entities (nearest to farthest): {', '.join(nearby_entities)}\n\n"
            self.nearby_entities = nearby_entities
        else:
            observation += f"Nearby entities (nearest to farthest): None\n\n"

        observation += f"Health: {health:.1f}/20\n\n"
        self.health = int(health)

        observation += f"Hunger: {hunger:.1f}/20\n\n"
        self.hunger = int(hunger)

        observation += f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n"

        observation += f"Equipment: {equipment}\n\n"
        self.equipment = equipment

        if inventory:
            observation += f"Inventory ({inventory_used}/36): {inventory}\n\n"
            self.inventory_rawdata = inventory
            self.inventory = self.process_inventory(inventory_rawdata = self.inventory_rawdata)
        else:
            observation += f"Inventory ({inventory_used}/36): Empty\n\n"

        observation += f"Date: {self.num_of_date}\n\n"
        observation += f"Task: {task}\n\n"
        observation += f"Subgoal: {subgoal}\n\n"
        observation += f"Subgoal Memory Success: {self.subgoal_memory_success}\n\n"
        observation += f"Subgoal Memory Failed: {self.subgoal_memory_failed}\n\n"

        self.recipe_agent.update_info(
            inventory = self.inventory,
            biome = self.biome,
            nearby_block = self.nearby_block,
            nearby_entities = self.nearby_entities,
            equipment = self.equipment,
            chat_log = self.chat_log,
            error = self.error
        )
        
        return observation


    def reset(self, task='', context="", reset_env=True, reset_mode="soft"):
        self.action_agent.reset()
        self.recipe_agent.reset()
        self.inventory_rawdata = {}
        self.inventory = {}
        self.subgoal_memory = []
        self.subgoal_memory_success = []
        self.subgoal_memory_failed = []
        self.step_count = 0
        self.nearby_block = []
        self.equipment = []
        self.biome = ""
        self.nearby_entities = []
        self.time_of_day = ""
        self.health = 20
        self.hunger = 20

        if reset_env:
            self.env.reset(
                options={
                    "mode": reset_mode,
                    "wait_ticks": self.env_wait_ticks,
                }
            )
        # step to peek an observation
        events = self.env.step(
            "bot.chat(`/time set ${getNextTime()}`);\n"
            + f"bot.chat('/difficulty {str(self.difficulty)}');\n"
            + "bot.chat('/spectate @s @p');\n"
        )
        minecraft_info = self.interpret_events(
            events=events,
        )
        print(f"\033[32m**** Minecraft Info [Reset] ****\n{minecraft_info}\033[0m")

    
    def close(self):
        self.env.close()


    def step(self, code, subgoal=None):
        self.step_count += 1
        print("Code in this step:\n", code)

        try:
            events = self.env.step(
                code,
                programs=self.programs(),
            )
            minecraft_info = self.interpret_events(
                events=events,
                code=code,
                task = self.next_task,
                subgoal = subgoal,
            )
            print(f"\033[32m**** Minecraft Info [Step] ****\n{minecraft_info}\033[0m")
            self.last_events = copy.deepcopy(events)
            
        except Exception as e:
            print(e)

        return
    
    # Recipe decomposition
    def rollout(self, task:dict):
        self.next_task = copy.deepcopy(task)
        print(f"\033[31m=================　SET TASK : {self.next_task} ====================\033[0m")
        iterations = 0
        try:
            task_done = False
            self.initial_inventory = self.inventory
            self.recipe_agent.update_initial_inventory(inventory=self.initial_inventory)
            while True:
                if iterations > self.max_iterations_rollout:
                    print("\nThe iterations reached the limitaion.\n")
                    print(f"\033[31m*******YOU FAILED THE TASK: {self.next_task}*******\033[0m")
                    self.failed_list.append(self.next_task)
                    success = False
                    break
                
                next_task = self.next_task

                subgoal, context = self.recipe_agent.set_current_goal(next_task)
                self.subgoal_memory.append(subgoal)

                # Retrieve codes from the past. If failed, regenerate it.
                if iterations > 0:
                    code = self.action_agent.get_action(
                        goal=subgoal, 
                        context=context, 
                        nearby_block=self.nearby_block, 
                        nearby_entities=self.nearby_entities, 
                        last_code=self.last_code, 
                        error_massage=self.error, 
                        chat_log=self.chat_log, 
                        retrieval=False
                    )
                else:
                    code = self.action_agent.get_action(
                        goal=subgoal, 
                        context=context, 
                        nearby_block=self.nearby_block, 
                        nearby_entities=self.nearby_entities, 
                        last_code="", 
                        error_massage=self.error, 
                        chat_log=self.chat_log, 
                        retrieval=True
                    )

                self.last_code = code
                self.last_context = context

                self.step(
                    code = code,
                    subgoal = subgoal,
                )

                subgoal_done = self.recipe_agent.complete_checker(subgoal)
                if subgoal_done:
                    print(f"\033[31m+++++++ SUBGOAL COMPLETED : {subgoal} +++++++\033[0m")
                    self.subgoal_memory_success.append(subgoal)
                    iterations = 0
                    self.error = ""
                    self.chat_log = ""
                    # 成功したactionおよびレシピの記録。あとで使い回すため
                    self.action_agent.save_action(subgoal, code)
                    self.recipe_agent.save_success_recipe(subgoal)
                    #　もともとinference関数で設定していた大目標の達成の確認
                    task_done = self.recipe_agent.complete_checker(self.next_task)
                    if task_done:
                        print(f"\033[31m*******TASK COMPLETED : {self.next_task}*******\033[0m")
                        self.success_list.append(self.next_task)
                        success = True
                        break
                else:
                    self.subgoal_memory_failed.append(subgoal)
                    iterations += 1
                    print(f"You faild the task: {subgoal}")
                    print(f"You are doing the same action for {iterations} times.")
                    #　タスクを失敗した場合に、recipe_agentの失敗リストに追加。回避するようにする。
                    self.recipe_agent.save_faild_recipe(subgoal)
                    #　3回連続で失敗したら、レシピをもう一度探索し直す。
                    if iterations > 0 and iterations % 3 == 0:
                        print("\nYou failed this task 5 times. Reset recipe.\n")
                        self.recipe_agent.reset_recipe()
        except Exception as e:
            print(e)
            success = False

        return success

    def inference(self, task=None, sub_goals=[], reset_mode="hard", reset_env=True):
        self.task_list = copy.deepcopy(task)
        print("TASK LIST: ",self.task_list)

        for item in self.task_list:
            self.reset(reset_env=reset_env, reset_mode=reset_mode)
            success = self.rollout(task=item)
            print("This is the final record of the inventory: ", self.inventory)
            self.record_log(success=success)
            self.close()
            
        print("ALL TASK COMPLETED")
        print("SUCCESS: ", self.success_list)
        print("FAILED: ", self.failed_list)
        return


    # ======== ROLE ========= 
    def inventory_inc(self, item_dict:dict, item_name:str):
        #増える分には増えすぎる可能性はそれなりにある→その場合は成功と判断
        if (item_name in self.inventory) and (item_name in self.initial_inventory) :
            diff = item_dict[item_name] - (self.inventory[item_name] - self.initial_inventory[item_name])
            if diff <= 0:
                return True
            else:
                return False
        elif item_name in self.inventory:
            diff = item_dict[item_name] - self.inventory[item_name]
            if diff <= 0:
                return True
            else:
                return False
        else:
            return False        
        
    def inventory_dec(self, item_dict:dict, item_name:str):
        #減る場合には、減りすぎているということは能動的に捨てる、またはそれに準ずるアクションをとっている可能性が高い→その場合は失敗と判断
        if (item_name in self.inventory) and (item_name in self.initial_inventory) :
            diff = item_dict[item_name] - (self.initial_inventory[item_name] - self.inventory[item_name])
            if diff == 0:
                return True
            else:
                return False
        elif item_name in self.initial_inventory:
            diff = item_dict[item_name] - self.initial_inventory[item_name]
            if diff == 0:
                return True
            else:
                return False
        else:
            return False  


    def create_daily_report(self):
        print("~~~~~~~~~~create_daily_report~~~~~~~~~~")
        report = f"""
        day : {self.num_of_date} \n
        achieved subgoal : {self.subgoal_memory_success} \n
        failed subgoal : {self.subgoal_memory_failed} \n
        final inventory : {self.inventory} \n
        errors : {self.error}\n
        chat log : {self.chat_log}\n
        """
        self.num_of_date = self.num_of_date + 1
        self.subgoal_memory_success = []
        self.subgoal_memory_failed = []
        self.chat_log = ""
        return report
    
    def execute_task_manually(self, task:dict):
        # functions which are used through Current Goal Algorithm in rollout
        rollout_functions =["craft", "mine", "smelt", "collect"]
        result_txt = ""

        self.initial_inventory = self.inventory
        
        if task["action"] in rollout_functions:
            next_task = {task["item_name"]:task["count"]}
            success = self.rollout(task=next_task)
        elif task["action"] == ["kill", "fish", "harvest"]:
            #別個に指定しないと達成が困難なアクション:その中でも実行後に特定アイテムの数の増加が予想されるタスク
            try :
                print(f"-------task name :{task['action']},  is being done.-------")
                code = f'await {task["action"]}(bot, {task["item_name"]}, {task["count"]});'
                self.step(code)
                self.final_inventory = self.inventory
                success = self.inventory_dec(item_dict=task, item_name="item_name")
            except Exception as e :
                print(f"Error occurred in execute_task:\n{e}")
                success = False
        elif task["action"] == ["tillAndPlant"]:
            #別個に指定しないと達成が困難なアクション:その中でも実行後に特定アイテムの数の減少が予想されるタスク
            try :
                print(f"-------task name :{task['action']},  is being done.-------")
                code = f'await {task["action"]}(bot, {task["item_name"]}, {task["count"]});'
                self.step(code)
                self.final_inventory = self.inventory
                success = self.inventory_dec(item_dict=task, item_name="item_name")
            except Exception as e :
                print(f"Error occurred in execute_task:\n{e}")
                success = False

        if success:
            result_txt =  f"I completed the task: {task['action']} {task['count']} {task['item_name']}."
        else:
            result_txt = f"I failed the task: {task['action']} {task['count']} {task['item_name']}."

        return result_txt
    
    def execute_task(self, task:dict):
        # If the function is in this list, use current goal algorithm to decompose recipes.
        rollout_functions =["craft", "mine", "smelt", "collect"]
        result_txt = ""

        self.initial_inventory = self.inventory

        if task["action"] in rollout_functions:
            next_task = {task["item_name"]:task["count"]}
            success = self.rollout(task=next_task)
            if success:
                result_txt =  f"I completed the task: {task['action']} {task['count']} {task['item_name']}."
            else:
                result_txt = f"I failed the task: {task['action']} {task['count']} {task['item_name']}."
        else:
            try:
                code = f'await {task["action"]}(bot, {task["item_name"]}, {task["count"]});'
                self.step(code=code)
                self.final_inventory = self.inventory
                result_txt = self.diary_agent.evaluate_result()
            except Exception as e :
                print(f"Error occurred in execute_task:\n{e}")
                result_txt = f"I failed the task: {task['action']} {task['count']} {task['item_name']}, because an error occurrred during task execution."
        
        return result_txt
    

    def inference_role(self, role, max_number_of_days, reset_mode="hard", reset_env=True):
        print("Role: ",role)
        self.role = role
        self.reset(reset_env=reset_env, reset_mode=reset_mode)
        
        for day in range(max_number_of_days):
            self.daily_executed_tasks = []
            self.num_of_date = day + 1
            self.diary_txt = f"DAY {self.num_of_date} : "
            
            # --- Generate Dream ---
            #self.dream =  "You are a farmer. Your job in Minecraft  is to collect seeds, craft a wooden_hoe, plant seeds, and harvest crops."
            self.dream = self.dream_agent.generate_dream(role=self.role, numofDate = self.num_of_date, lastDream=self.dream, inventory=self.final_inventory, memory=self.memory)
            print(f"\033[34m\n**** Dream ****\n\nDAY {self.num_of_date}\n\nDream:\n{self.dream}\n\033[0m")

            # --- Generate Today's Goal TODO_list ---
            # self.todaysgoal = ["craft wooden_hoe", "Plant crops", "Build a basic structure"]
            self.todaysgoal = self.role_agent.make_todaysgoal(self.dream, self.inventory, self.memory)   
            print(f"\033[34m\n**** Today's Goal ****\n\nDAY {self.num_of_date}\n\nToday's Goal:\n{self.todaysgoal}\n\033[0m")  

            for todo in self.todaysgoal:
                # --- Generate TODO_datail ---
                #self.todo_detail = [{"action": "collect", "item_name": "wheat_seeds", "count": 1}]
                self.todo_detail = self.role_agent.make_todo_detail(self.dream, todo, self.inventory, self.memory)
                print(f"\033[34m\n**** TODO datail ****\n\nDAY {self.num_of_date}\n\nTODO:\n{todo}\n\nTODO detail:\n{self.todo_detail}\n\033[0m")  
                self.daily_executed_tasks += self.todo_detail

                for task in self.todo_detail:
                    # --- Execute Task ---
                    print(f"Set task from TODO detail: {task}\n")
                    result_txt = self.execute_task(task=task)
                    # result_txt = self.execute_task_manually(task=task)

                    self.diary_txt += result_txt

                    print("This is the final record of the inventory: ", self.inventory)
                    self.record_log(success=result_txt, todo=todo)

            # self.final_inventory = self.inventory
            #daily_result = self.diary_agent.generate_diary(self.initial_inventory, self.final_inventory, self.daily_executed_tasks, self.num_of_date)#self.create_daily_report()
            #self.memory += daily_result
            #print(daily_result)   
            self.memory.append(self.diary_txt)
            print(f"\033[31m\n**** Day {self.num_of_date} END ****\n{self.memory}\n\033[0m")

        return
                    
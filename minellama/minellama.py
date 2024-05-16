import copy
import json
import os
import time
from typing import Dict
from datetime import datetime

import minellama.utils as U
from .env import VoyagerEnv

from .agents import DecisionMaker
from .agents import DecisionMakerLLM


class Minellama:
    def __init__(
        self,
        mc_port: int = None, # Minecraft port
        azure_login: Dict[str, str] = None,
        server_port: int = 3000,
        openai_api_key: str = None, # OpenAI API Key
        env_wait_ticks: int = 20,
        env_request_timeout: int = 600,
        max_iterations: int = 10, # Max iterations for each task. If reached it, it skips the task to the next.
        reset_placed_if_failed: bool = False,
        difficulty: str = "peaceful", # Difficulty of Minecraft game
        llm: str = None, # "llama", "gpt", or None
        llm_model: str = None, # "meta-llama/Llama-2-70b-chat-hf" for Llama2, "gpt-3.5-turbo" or "gpt-4" for GPT
        local_llm_path: str = None, # If you have local Llama2, set the path to the directory. If None, it will create the model dir in minellama/llm/ .
        hf_auth_token: str = "", # Hugging face auth token.
        record_file: str = "./log.txt", # the output file to record the result.
    ):
        # init env
        self.env = VoyagerEnv(
            mc_port=mc_port,
            azure_login=azure_login,
            server_port=server_port,
            request_timeout=env_request_timeout,
        )
        self.env_wait_ticks = env_wait_ticks
        self.reset_placed_if_failed = reset_placed_if_failed
        self.max_iterations = max_iterations

        # # set openai api key
        if openai_api_key is not None:
            os.environ["OPENAI_API_KEY"] = openai_api_key

        if llm is not None:
            self.decision_maker = DecisionMakerLLM(llm=llm, llm_model=llm_model, hf_auth_token=hf_auth_token, local_llm_path=local_llm_path)
        else:
            # This is for baseline without LLM
            self.decision_maker = DecisionMaker()
        self.llm = llm

        # init variables for rollout
        self.action_agent_rollout_num_iter = -1
        self.task = None
        self.context = ""
        self.messages = None
        self.conversations = []
        self.last_events = None
        self.skills = []
        self.skill_count = 0

        self.inventory = {}
        self.nearby_block = []
        self.equipment = []
        self.biome = ""
        self.nearby_entities = []
        self.last_code = ""
        self.iterations = 0

        self.success_list = []
        self.failed_list = []
        self.difficulty = difficulty
        self.task_list = []
        self.next_task = {}
        self.subgoal_memory = []
        self.step_count = 0
        self.chat_log = ""
        self.error = ""

        self.record_file = record_file 
        with open(self.record_file, "a") as f:
            formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n=========== The record at {formatted_datetime} ============\n")

    def event_reader(
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
        else:
            error = ""
            observation += f"Execution error: No error\n\n"

        if chat_messages:
            chat_log = "\n".join(chat_messages)
            observation += f"Chat log: {chat_log}\n\n"
        else:
            chat_log = ""
            observation += f"Chat log: None\n\n"

        observation += f"Biome: {biome}\n\n"

        observation += f"Time: {time_of_day}\n\n"

        if voxels:
            observation += f"Nearby blocks: {', '.join(voxels)}\n\n"
        else:
            observation += f"Nearby blocks: None\n\n"

        if entities:
            nearby_entities = [
                k for k, v in sorted(entities.items(), key=lambda x: x[1])
            ]
            observation += f"Nearby entities (nearest to farthest): {', '.join(nearby_entities)}\n\n"
        else:
            observation += f"Nearby entities (nearest to farthest): None\n\n"

        observation += f"Health: {health:.1f}/20\n\n"

        observation += f"Hunger: {hunger:.1f}/20\n\n"

        observation += f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n"

        observation += f"Equipment: {equipment}\n\n"

        if inventory:
            observation += f"Inventory ({inventory_used}/36): {inventory}\n\n"
        else:
            observation += f"Inventory ({inventory_used}/36): Empty\n\n"

        observation += f"Task: {task}\n\n"
        observation += f"Subgoal: {subgoal}\n\n"

        self.inventory = inventory
        self.error = error
        self.chat_log = chat_log

        return observation


    def reset(self, task='', context="", reset_env=True):
        if reset_env:
            self.env.reset(
                options={
                    "mode": "soft",
                    "wait_ticks": self.env_wait_ticks,
                }
            )
        # step to peek an observation
        events = self.env.step(
            "bot.chat(`/time set ${getNextTime()}`);\n"
            + f"bot.chat('/difficulty {str(self.difficulty)}');\n"
            + "bot.chat('/spectate @s @p');\n"
        )

        human_message = self.event_reader(
            events=events,
        )
        print(f"\033[32m****Human message****\n{human_message}\033[0m")
        self.decision_maker.reset_memory()
        self.inventory = {}
        self.decision_maker.update_inventory(inventory=self.inventory)
        self.subgoal_memory = []
        self.step_count = 0
        self.iterations = 0
        self.error = ""
        self.chat_log = ""

        return 
    
    def close(self):
        self.env.close()

    def step(self, code, subgoal=None):
        self.step_count += 1
        print("Code in step:\n", code)

        try:
            events = self.env.step(
                code,
                programs=self.decision_maker.programs,
            )
            self.last_code = code

            human_message = self.event_reader(
                events=events,
                code=code,
                task = self.next_task,
                subgoal = subgoal,
            )

            print(f"\033[32m****Human message****\n{human_message}\033[0m")
            self.last_events = copy.deepcopy(events)
            
        except Exception as e:
            print(e)

        return
    

    def rollout(self, *, reset_env=True):
        self.reset(reset_env=reset_env)
        task_done = False
        while True:
            if self.iterations > self.max_iterations:
                print("\nThe iterations reached the limitaion.\n")
                print(f"\033[31m*******YOU FAILED THE TASK: {self.next_task}*******\033[0m")
                self.failed_list.append(self.next_task)
                success = False
                break
            next_task = self.next_task

            #With or without LLM. コード生成に関してllmなしの場合と統一できていないため
            if self.llm is not None:
                next_subgoal = self.decision_maker.set_current_goal(next_task)
                self.subgoal_memory.append(next_subgoal)
                #Retrieve codes from the past. If failed, regenerate it.
                if self.iterations > 0:
                    code = self.decision_maker.code_generator(goal=next_subgoal, retrieval=False)
                else:
                    code = self.decision_maker.code_generator(goal=next_subgoal, retrieval=True)
            else:
                code = self.decision_maker.set_current_goal(next_task)

            self.step(
                code = code,
                subgoal = next_subgoal,
            )
            self.decision_maker.update_inventory(inventory=self.inventory)
            subgoal_done = self.decision_maker.complete_checker(next_subgoal)
            if subgoal_done:
                print(f"+++++++SUBGOAL COMPLETED : {next_subgoal}+++++++")
                self.iterations = 0
                if self.llm is not None:
                    self.decision_maker.save_action(next_subgoal, code)
                task_done = self.decision_maker.complete_checker(self.next_task)
                if task_done:
                    print(f"\033[31m*******TASK COMPLETED : {self.next_task}*******\033[0m")
                    self.success_list.append(self.next_task)
                    success = True
                    #just to show up the item on the right hand.
                    self.step(
                        code = f"await showBlock(bot, '{list(self.next_task.keys())[0]}')",
                    )
                    break
            else:
                self.iterations += 1
                print(f"You are doing the same action for {self.iterations} times.")
                if self.error != "":
                    del self.decision_maker.recipes[list(next_subgoal.keys())[0]]
                    print(f"Deleted {list(next_subgoal.keys())[0]} from the recipe list.")
        return success


    def inference(self, task=None, sub_goals=[], reset_mode="hard", reset_env=True):
        self.task_list = copy.deepcopy(task)
        print("TASK LIST: ",self.task_list)
        for item in self.task_list:
            self.inventory = {}
            self.env.reset(
                options={
                    "mode": reset_mode,
                    "wait_ticks": self.env_wait_ticks,
                }
            )
            self.last_events = self.env.step("")
            self.next_task = copy.deepcopy(item)
            print(f"\033[31m=================SET GOAL : {self.next_task} ====================\033[0m")
            success = self.rollout(
                reset_env=reset_env,
            )
            print("This is the final record of the inventory: ", self.inventory)
            with open(self.record_file, "a") as f:
                f.write(f"\n\nTASK: {self.next_task}\nSUCCESS: {success}\nINVENTORY: {self.inventory}\nSUBGOAL_MEMORY: {self.subgoal_memory}\nACTION_MEMORY: {self.decision_maker.memory}\nLAST_CODE_AND_CONTEXT: {self.decision_maker.current_code} {self.decision_maker.current_context}\nSTEP_COUNT: {self.step_count}\nTIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            self.close()
            
        print("ALL TASK COMPLETED")
        print("SUCCESS: ", self.success_list)
        print("FAILED: ", self.failed_list)
        return




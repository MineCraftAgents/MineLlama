from minellama.env import VoyagerEnv
from minellama.control_primitives import load_control_primitives
import json

# get all js action programs from minellama/control_primitives  -> str
control_primitives = load_control_primitives()
programs = ""
for primitives in control_primitives:
    programs += f"{primitives}\n\n"


#========= settings ===========
mc_port="35117"
server_port="3000"
env_request_timeout = 6000
env = VoyagerEnv(
    mc_port=mc_port,
    server_port=server_port,
    request_timeout=env_request_timeout,
)

#========= initialize ========
env.reset(
    options={
        "mode": "hard",
        "wait_ticks": 20
    }
)
print("!reset!")

# step to peek an observation
events = env.step(
    "bot.chat(`/time set ${getNextTime()}`);\n"
    + "bot.chat('/spectate @s @p');\n"
)
print(f"events:{events}")



#========= EXAMPLE: step with code ==============
# Here are javascript functions:
# 1) craft(bot, item, count); //Use this to craft item. 
# 2) smelt(bot, item, count, fuel); //Use this to smelt item. fuel should be 'planks'.
# 3) mine(bot, item, count, tool); //Use this to mine item. When you need tools to mine, give it as an argument, e.g. 'wooden_pickaxe' to mine stone.
# 4) kill(bot, entity, count, tool); //Use this to get item by killing entities. When you need tools to kill, give it as an argument, e.g. 'wooden_sword'.
# events = env.step(
#     code= "await mine(bot, 'log',1);",
#     programs= programs
# )
# print(f"events:{events}\n")

#==============================================

#function to format events
# def format_data(data):
#     formatted_str = ""
#     for key, value in data.items():
#         if isinstance(value, dict):
#             formatted_str += f"{key}: {json.dumps(value, separators=(',', ': '), ensure_ascii=False)}\n"
#         else:
#             formatted_str += f"{key}: {value}\n"
#     return formatted_str.strip()

def event_reader(
        *, events, code="", task="", subgoal="", context="", critique=""
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
            observation += f"Execution error: No error\n\n"

        if chat_messages:
            chat_log = "\n".join(chat_messages)
            observation += f"Chat log: {chat_log}\n\n"
        else:
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
        
        return observation

#=========== steps with multiple codes ============
codes = [
    "await tillAndPlant(bot, 'wheat_seeds', 5);",
    "await harvest(bot, 'wheat', 1);"
    # "await mine(bot, 'log',3);",
    # "await craft(bot, 'planks',13)",
    # "await craft(bot, 'crafting_table', 1)",
    # "await craft(bot, 'stick', 6)",
    # "await craft(bot, 'wooden_pickaxe', 1)",
    # "await mine(bot, 'cobblestone', 3, 'wooden_pickaxe')",
    # "await craft(bot, 'stone_pickaxe',1)",
    # "await mine(bot, 'cobblestone', 8, 'stone_pickaxe')",
    # "await mine(bot, 'raw_iron', 3, 'stone_pickaxe')",
    # "await craft(bot, 'furnace',1)",
    # "await smelt(bot, 'raw_iron', 2, 'planks')",
    # "await craft(bot, 'iron_sword', 1)",
    # "await kill(bot, 'cow', 1, 'iron_sword')"
]

for code in codes:
    print(f"code: {code}")
    events = env.step(
        code= code,
        programs= programs
    )
    # print(f"events:{events}\n")
    # obs = format_data(events[-1][1])
    obs = event_reader(events=events, code=code)
    print(f"observation:\n{obs}\n")



env.close()


# for i in range (10):
#     print(f"i:{i}")
#     env.step(code= "await mine(bot, 'log',1);")

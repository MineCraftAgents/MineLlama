from minellama.env import VoyagerEnv
from minellama.control_primitives import load_control_primitives
import json

# get all js action programs from minellama/control_primitives  -> str
control_primitives = load_control_primitives()
programs = ""
for primitives in control_primitives:
    programs += f"{primitives}\n\n"


#========= settings ===========
mc_port="MINECRAFT_PORT_NUMBER"
server_port="3000"
env_request_timeout = 600
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
events = env.step(
    code= "await mine(bot, 'log',1);",
    programs= programs
)
print(f"events:{events}\n")

#==============================================

#function to format events
def format_data(data):
    formatted_str = ""
    for key, value in data.items():
        if isinstance(value, dict):
            formatted_str += f"{key}: {json.dumps(value, separators=(',', ': '), ensure_ascii=False)}\n"
        else:
            formatted_str += f"{key}: {value}\n"
    return formatted_str.strip()

#=========== steps with multiple codes ============
codes = [
    "await mine(bot, 'log',3);",
    "await craft(bot, 'planks',13)",
    "await craft(bot, 'crafting_table', 1)",
    "await craft(bot, 'stick', 6)",
    "await craft(bot, 'wooden_pickaxe', 1)",
    "await mine(bot, 'cobblestone', 3, 'wooden_pickaxe')",
    "await craft(bot, 'stone_pickaxe',1)",
    "await mine(bot, 'cobblestone', 8, 'stone_pickaxe')",
    "await mine(bot, 'raw_iron', 3, 'stone_pickaxe')",
    "await craft(bot, 'furnace',1)",
    "await smelt(bot, 'raw_iron', 2, 'planks')",
    "await craft(bot, 'iron_sword', 1)",
    "await kill(bot, 'cow', 1, 'iron_sword')"
]

for code in codes:
    print(f"code: {code}")
    events = env.step(
        code= code,
        programs= programs
    )
    # print(f"events:{events}\n")
    obs = format_data(events[-1][1])
    print(f"observation:\n{obs}\n")



env.close()


# for i in range (10):
#     print(f"i:{i}")
#     env.step(code= "await mine(bot, 'log',1);")

import re
import json
from pathlib import Path

#このファイルはtodoを細かく分解して進めていく方式のもの

# role_explanation = """
# You are a smith, who mainly create iron_pickaxe.
# """


class RoleAgent:
    def __init__(self, llm):
        self.llm = llm

        data_path = ""
        data_path = str(Path(__file__).parent / data_path)
        with open(f"{data_path}/minecraft_dataset/items.json", "r") as f:
            mc_items_json = json.load(f)
            self.mc_items = {item['name']: item for item in mc_items_json}

        self.role_prompt = """
        You are playing a role in Minecraft game.
        I want you to plan the next task.
        Each time, I give you information below:
        Role: ... ;This is your role in Minecraft.
        Invenotory: {{"ITEM_NAME":COUNT,...}}
        Memory: [{{"TASK":COUNT}},...] ;Those are the tasks you achieved before.

        You must follow the python-dict like format below when you answer:
        {{"ITEM_NAME":COUNT}}

        Here is an example:
        {{"diamond_sword":3}}
        """

    def extract_list_from_str(self,response):
        matched = re.search(r'(\[.*?\])', response, re.DOTALL)
        if matched:
            json_list = matched.group(1).strip()
            # print("json_list: ",json_list)
            return json.loads(json_list)
        else:
            print("No list found. Trying again.")
            return None

    def item_name_checker(self, json_dict):
        name = list(json_dict.keys())[0]
        if name == "logs":
            task = {"log":json_dict[name]}
        if name == "plank":
            task = {"planks":json_dict[name]}
        if name == "sticks":
            task = {"stick":json_dict[name]}
        else:
            task = {name:json_dict[name]}
        return task

    def check_item_name(self, name:str):
        if name in self.mc_items:
            print(self.mc_items[name])
            return True
        else :
            return False

    def make_todaysgoal(self, dream, inventory, memory, error_message="none", max_iterations=10):
        system_prompt_todo = """
        You are assisting with role-playing in the Minecraft game.

        Your task is to translate the given role text into a TO-DO list for today (in Python list format) that represents the goal.

        Each time, you will be given:

        Role: This is the role the player has been assigned.
        Inventory: {{"ITEM_NAME":COUNT,...}} — These are the items the player currently has.
        Memory: [{{"TASK":COUNT}},...] — These are the tasks you have completed before.
        Error_Message: This is the error message fromt the last round.

        Your goal is to determine and output a TO-DO list for today that the player should have to complete the given role. The output should be in the following format:
        ["Action1", "Action2",...]

        However, the actions you can do in this Minecraft game are limitied. Here are the possible actions:
        Collect, craft, plant, harvest, fish, kill, smelt.

        Please follow these instructions:

        1.Use accurate Minecraft item names, and avoid ambiguous terms such as fertilizer, animal, food, tool or material.
        2.Provide your answers in the format of a Python list.
        3.Clarify the action for each TO-DO. For example, "Collect log", "Craft stone_sword", or "Harvest wheat".
        4.The TO-DO list is only for today. Don't make too much.
        5.Only provide the answer in the specified format and do not include additional explanations or comments.
        6.The length of output-list should be 1 or 2.
        """
        
        iterations = 0
        error_message = ""
        while iterations < max_iterations:
            print("Making Today's Goal...")
            human_prompt_todo = f"Role: {dream} Inventory: {inventory} Memory: {memory}, Error_message: {error_message}, what does the player have to do today to complete role playing? "
            # print(human_prompt_todo)
            try :
                response = self.llm.content(system_prompt_todo, query_str=human_prompt_todo, data_dir="recipe")
                # print("response:",response)
                extracted_response = self.extract_list_from_str(response)
                if extracted_response is not None:
                    return extracted_response
                else:
                    error_message = "Invalid Error. No list found."
            except Exception as e :
                print("Unexpected error was occured. Trying again ...")
                continue
        
        return extracted_response
    
    def make_todo_detail(self, dream, todo, inventory, memory, max_iterations=10):
        system_prompt_todo_detail = """
        You are providing support for Minecraft gameplay. Your task is to output the actions the player should take in Minecraft based on the given short sentences according to the instructions below. The output should be a list with elements of type Python dict. Each dict should have the format:
        [{{"action": action name, "item_name": name of the item, "count": number of items}}]
        Each time, you will be given:
        To Do: The general goal the player wants to achieve.
        Inventory: {{"ITEM_NAME": COUNT, ...}} — These are the items the player currently has.
        Memory: [{{"TASK": COUNT}}, ...] — These are the tasks you have completed before.
        Error_Message: This is the error message fromt the last round.

        What you can do is here. You must choose one of these actions when you choose "action".
        1) craft :Use this to craft item. 
        2) smelt:Use this to smelt item.
        3) mine:Use this to mine block. 
        4) collect:Use this to collect item.
        5) kill:Use this to get item by killing entities. 
        6) fish:Use this to catch fish.
        7) tillAndPlant :Use this to plant seeds. You need seeds and hoe first. You will find and go to water, till  farmland with hoe, and plant seeds with this function.
        8) harvest:Use this to harvest wheat. You have to plant seeds first. You will wait for wheat around you to grow and harvest them with this.

        Please follow these guidelines when creating your output:
        1. Use item names that exist within Minecraft. For example: stone_pickaxe.
        2. The output should be in the format of a Python list. Each element should be a dict in the previously mentioned format: [{{"action": action name, "item_name": name of the item, "count": number of items}}]. For example: `[{{"action": "mine", "item_name": "cobblestone", "count": 3}}].
        3. For action name, choose from ["craft", "mine", "smelt", "collect", "kill", "fish", "tillAndPlant", "harvest"]. Do not use any other names.
        4. Do not output answers that are not listed above. No additional explanations or clarifications are needed.
        5. Under no circumstances should there be any line breaks.
        5.The length of output-list should be 1 or 2.
        """
        
        #[{{"action": "mine", "item_name": "cobblestone", "count": 3}}, {{"action": "craft", "item_name": "stick", "count": 2}}, {{"action": "craft", "item_name": "stone_pickaxe", "count": 1}}]
        #Dream : Your role. you have to fullfill this order.
        #Here is the minecraft item name list. You must use these item nemes.
        #["stone","grass","dirt","cobblestone","planks","sapling","bedrock","sand","gravel","gold_ore","iron_ore","coal_ore","log","leaves","sponge","glass","lapis_ore","lapis_block","dispenser","sandstone","noteblock","golden_rail","detector_rail","sticky_piston","web","tallgrass","deadbush","piston","wool","yellow_flower","red_flower","brown_mushroom","red_mushroom","gold_block","iron_block","stone_slab","brick_block","tnt","bookshelf","mossy_cobblestone","obsidian","torch","mob_spawner","oak_stairs","chest","diamond_ore","diamond_block","crafting_table","farmland","furnace","ladder","rail","stone_stairs","lever","stone_pressure_plate","wooden_pressure_plate","redstone_ore","redstone_torch","stone_button","snow_layer","ice","snow","cactus","clay","jukebox","fence","pumpkin","netherrack","soul_sand","glowstone","lit_pumpkin","stained_glass","trapdoor","monster_egg","stonebrick","brown_mushroom_block","red_mushroom_block","iron_bars","glass_pane","melon_block","vine","fence_gate","brick_stairs","stone_brick_stairs","mycelium","waterlily","nether_brick","nether_brick_fence","nether_brick_stairs","enchanting_table","end_portal_frame","end_stone","dragon_egg","redstone_lamp","wooden_slab","sandstone_stairs","emerald_ore","ender_chest","tripwire_hook","emerald_block","spruce_stairs","birch_stairs","jungle_stairs","command_block","beacon","cobblestone_wall","wooden_button","anvil","trapped_chest","light_weighted_pressure_plate","heavy_weighted_pressure_plate","daylight_detector","redstone_block","quartz_ore","hopper","quartz_block","quartz_stairs","activator_rail","dropper","stained_hardened_clay","stained_glass_pane","leaves2","log2","acacia_stairs","dark_oak_stairs","slime","barrier","iron_trapdoor","prismarine","sea_lantern","hay_block","carpet","hardened_clay","coal_block","packed_ice","double_plant","red_sandstone","red_sandstone_stairs","stone_slab2","spruce_fence_gate","birch_fence_gate","jungle_fence_gate","dark_oak_fence_gate","acacia_fence_gate","spruce_fence","birch_fence","jungle_fence","dark_oak_fence","acacia_fence","end_rod","chorus_plant","chorus_flower","purpur_block","purpur_pillar","purpur_stairs","purpur_slab","end_bricks","grass_path","repeating_command_block","chain_command_block","iron_shovel","iron_pickaxe","iron_axe","flint_and_steel","apple","bow","arrow","coal","diamond","iron_ingot","gold_ingot","iron_sword","wooden_sword","wooden_shovel","wooden_pickaxe","wooden_axe","stone_sword","stone_shovel","stone_pickaxe","stone_axe","diamond_sword","diamond_shovel","diamond_pickaxe","diamond_axe","stick","bowl","mushroom_stew","golden_sword","golden_shovel","golden_pickaxe","golden_axe","string","feather","gunpowder","wooden_hoe","stone_hoe","iron_hoe","diamond_hoe","golden_hoe","wheat_seeds","wheat","bread","leather_helmet","leather_chestplate","leather_leggings","leather_boots","chainmail_helmet","chainmail_chestplate","chainmail_leggings","chainmail_boots","iron_helmet","iron_chestplate","iron_boots","diamond_helmet","diamond_chestplate","diamond_leggings","diamond_boots","golden_helmet","golden_chestplate","golden_leggings","flint","porkchop","cooked_porkchop","painting","golden_apple","sign","wooden_door","bucket","water_bucket","lava_bucket","minecart","saddle","iron_door","redstone","snowball","boat","leather","milk_bucket","brick","clay_ball","reeds","paper","book","slime_ball","chest_minecart","furnace_minecart","egg","compass","fishing_rod","clock","glowstone_dust","fish","cooked_fish","dye","bone","sugar","cake","bed","repeater","cookie","filled_map","shears","melon","pumpkin_seeds","melon_seeds","beef","cooked_beef","chicken","cooked_chicken","rotten_flesh","ender_pearl","blaze_rod","ghast_tear","gold_nugget","nether_wart","potion","glass_bottle","spider_eye","fermented_spider_eye","blaze_powder","magma_cream","brewing_stand","cauldron","ender_eye","speckled_melon","spawn_egg","experience_bottle","fire_charge","writable_book","written_book","emerald","item_frame","flower_pot","carrot","potato","baked_potato","poisonous_potato","map","golden_carrot","skull","carrot_on_a_stick","nether_star","pumpkin_pie","fireworks","firework_charge","enchanted_book","comparator","netherbrick","quartz","tnt_minecart","hopper_minecart","prismarine_shard","prismarine_crystals","rabbit","cooked_rabbit","rabbit_stew","rabbit_foot","rabbit_hide","armor_stand","iron_horse_armor","golden_horse_armor","diamond_horse_armor","lead","name_tag","command_block_minecart","mutton","cooked_mutton","banner","end_crystal","spruce_door","birch_door","jungle_door","acacia_door","dark_oak_door","chorus_fruit","chorus_fruit_popped","beetroot","beetroot_seeds","beetroot_soup","dragon_breath","splash_potion","spectral_arrow","tipped_arrow","lingering_potion","shield","elytra","spruce_boat","birch_boat","jungle_boat","acacia_boat","dark_oak_boat","record_13","record_cat","record_blocks","record_chirp","record_far","record_mall","record_mellohi","record_stal","record_strad","record_ward","record_11","record_wait"]
        
        #Dream:{dream}, 
        print("Making TODO details...")
        iterations = 0
        error_message = ""
        while iterations < max_iterations:
            human_prompt_todo_detail = f"To Do: {todo}, Inventory: {inventory} Memory: {memory}, error messagae:{error_message}, what does the player have to do today? "#
            error_message = ""#各ループでエラーをリセットしないと、本質の部分が希薄になる
            # print(human_prompt_todo_detail)
            try :
                response = self.llm.content(system_prompt_todo_detail, query_str=human_prompt_todo_detail, data_dir="recipe")
                print("response:",response)
                extracted_response = self.extract_list_from_str(response)
            except Exception as e:
            # 予期しないエラーをキャッチする
                print(f"Unexpected error occurred. Moving to the next iteration.")
                continue
            if extracted_response is not None:
                func_list=["craft", "mine", "smelt", "collect", "kill", "fish", "tillAndPlant", "harvest"]
                itemname_list = ["stone","grass","dirt","cobblestone","planks","sapling","bedrock","sand","gravel","gold_ore","iron_ore","coal_ore","log","leaves","sponge","glass","lapis_ore","lapis_block","dispenser","sandstone","noteblock","golden_rail","detector_rail","sticky_piston","web","tallgrass","deadbush","piston","wool","yellow_flower","red_flower","brown_mushroom","red_mushroom","gold_block","iron_block","stone_slab","brick_block","tnt","bookshelf","mossy_cobblestone","obsidian","torch","mob_spawner","oak_stairs","chest","diamond_ore","diamond_block","crafting_table","farmland","furnace","ladder","rail","stone_stairs","lever","stone_pressure_plate","wooden_pressure_plate","redstone_ore","redstone_torch","stone_button","snow_layer","ice","snow","cactus","clay","jukebox","fence","pumpkin","netherrack","soul_sand","glowstone","lit_pumpkin","stained_glass","trapdoor","monster_egg","stonebrick","brown_mushroom_block","red_mushroom_block","iron_bars","glass_pane","melon_block","vine","fence_gate","brick_stairs","stone_brick_stairs","mycelium","waterlily","nether_brick","nether_brick_fence","nether_brick_stairs","enchanting_table","end_portal_frame","end_stone","dragon_egg","redstone_lamp","wooden_slab","sandstone_stairs","emerald_ore","ender_chest","tripwire_hook","emerald_block","spruce_stairs","birch_stairs","jungle_stairs","command_block","beacon","cobblestone_wall","wooden_button","anvil","trapped_chest","light_weighted_pressure_plate","heavy_weighted_pressure_plate","daylight_detector","redstone_block","quartz_ore","hopper","quartz_block","quartz_stairs","activator_rail","dropper","stained_hardened_clay","stained_glass_pane","leaves2","log2","acacia_stairs","dark_oak_stairs","slime","barrier","iron_trapdoor","prismarine","sea_lantern","hay_block","carpet","hardened_clay","coal_block","packed_ice","double_plant","red_sandstone","red_sandstone_stairs","stone_slab2","spruce_fence_gate","birch_fence_gate","jungle_fence_gate","dark_oak_fence_gate","acacia_fence_gate","spruce_fence","birch_fence","jungle_fence","dark_oak_fence","acacia_fence","end_rod","chorus_plant","chorus_flower","purpur_block","purpur_pillar","purpur_stairs","purpur_slab","end_bricks","grass_path","repeating_command_block","chain_command_block","iron_shovel","iron_pickaxe","iron_axe","flint_and_steel","apple","bow","arrow","coal","diamond","iron_ingot","gold_ingot","iron_sword","wooden_sword","wooden_shovel","wooden_pickaxe","wooden_axe","stone_sword","stone_shovel","stone_pickaxe","stone_axe","diamond_sword","diamond_shovel","diamond_pickaxe","diamond_axe","stick","bowl","mushroom_stew","golden_sword","golden_shovel","golden_pickaxe","golden_axe","string","feather","gunpowder","wooden_hoe","stone_hoe","iron_hoe","diamond_hoe","golden_hoe","wheat_seeds","wheat","bread","leather_helmet","leather_chestplate","leather_leggings","leather_boots","chainmail_helmet","chainmail_chestplate","chainmail_leggings","chainmail_boots","iron_helmet","iron_chestplate","iron_boots","diamond_helmet","diamond_chestplate","diamond_leggings","diamond_boots","golden_helmet","golden_chestplate","golden_leggings","flint","porkchop","cooked_porkchop","painting","golden_apple","sign","wooden_door","bucket","water_bucket","lava_bucket","minecart","saddle","iron_door","redstone","snowball","boat","leather","milk_bucket","brick","clay_ball","reeds","paper","book","slime_ball","chest_minecart","furnace_minecart","egg","compass","fishing_rod","clock","glowstone_dust","fish","cooked_fish","dye","bone","sugar","cake","bed","repeater","cookie","filled_map","shears","melon","pumpkin_seeds","melon_seeds","beef","cooked_beef","chicken","cooked_chicken","rotten_flesh","ender_pearl","blaze_rod","ghast_tear","gold_nugget","nether_wart","potion","glass_bottle","spider_eye","fermented_spider_eye","blaze_powder","magma_cream","brewing_stand","cauldron","ender_eye","speckled_melon","spawn_egg","experience_bottle","fire_charge","writable_book","written_book","emerald","item_frame","flower_pot","carrot","potato","baked_potato","poisonous_potato","map","golden_carrot","skull","carrot_on_a_stick","nether_star","pumpkin_pie","fireworks","firework_charge","enchanted_book","comparator","netherbrick","quartz","tnt_minecart","hopper_minecart","prismarine_shard","prismarine_crystals","rabbit","cooked_rabbit","rabbit_stew","rabbit_foot","rabbit_hide","armor_stand","iron_horse_armor","golden_horse_armor","diamond_horse_armor","lead","name_tag","command_block_minecart","mutton","cooked_mutton","banner","end_crystal","spruce_door","birch_door","jungle_door","acacia_door","dark_oak_door","chorus_fruit","chorus_fruit_popped","beetroot","beetroot_seeds","beetroot_soup","dragon_breath","splash_potion","spectral_arrow","tipped_arrow","lingering_potion","shield","elytra","spruce_boat","birch_boat","jungle_boat","acacia_boat","dark_oak_boat","record_13","record_cat","record_blocks","record_chirp","record_far","record_mall","record_mellohi","record_stal","record_strad","record_ward","record_11","record_wait"]
                done = 0
                for item in extracted_response:
                    try:
                        if item['action'] not in func_list:
                            error_message += f"There is no action called {item['action']}.\n"
                            print(f"\nThere is no action called {item['action']}.\n")
                            done += 1 
                        if item['item_name'] not in itemname_list:
                            error_message += f"There is no item called {item['item_name']}.\n"
                            print(f"\nThere is no item called {item['item_name']}.\n")
                            done += 1
                    except Exception as e:
                        error_message += f'Format was invaild. Please use the format [{{"action": action name, "item_name": name of the item, "count": number of items}}]\n'
                        print(f"\nFormat was invalid.\n")
                        done += 1
                if done == 0:
                    return extracted_response
                #error_message += f'This is your response from last round: {extracted_response}\n'
                print(f'\nThis is your response from last round: {extracted_response}\n')
            else:
                error_message += f"Invalid Error. No list found.\n"
                print(f"\nInvalid Error. No list found.\n")
        
        #LLMの出力が不安定なので、本当に一度も有効な回答が手に入らなかった場合の緊急措置。どのタスクにも要求されるアイテムを補充する。        
        instant_task = [{"action": "craft", "item_name": "crafting_table", "count": 1}, {"action": "mine", "item_name": "log", "count": 5}, {"action": "mine", "item_name": "cobblestone", "count": 5}]
        return instant_task
    
    
    #todo_detailを作成する場合、next_taskは役割がかぶるので不要になる？    
    def next_task(self, role, todaysgoal, inventory, memory=None):
        print("~~~~~~~~~~next task~~~~~~~~~~~")
        system_prompt = self.role_prompt
        human_prompt = f"Today's goal: {todaysgoal} Inventory: {inventory} Memory: {memory} What is the next task?"
        response = self.llm.content(system_prompt, query_str=human_prompt, data_dir="action")
        print(response)
        extracted_response = self.extract_dict_from_str(response)
        # print(extracted_response)
        return extracted_response
import recipe_agent as ra
import copy
import json
from collections import defaultdict

agent = ra.RecipeAgent()

todaysgoal_list = ["stone_pickaxe", "stone_sword", "iron_pickaxe"]

expect_final_inventory = copy.deepcopy(todaysgoal_list)

#採取に必要になるツールが存在すればそれを調べ上げ、そのツールに対してもレシピ分解を行う関数
def get_full_dependance(final_inventory):
    num = 0
    result = []
    agent = ra.RecipeAgent()
    # final_inventoryのコピーを作成して処理する
    inventory_copy = final_inventory.copy()
    
    while num < len(inventory_copy):
        item = inventory_copy[num]
        recipe = agent.get_recipe_list_for_export(item)
        
        for r in recipe:
            for ingredient in r:
                tool = agent.required_tool(list(ingredient.keys())[0])
                if tool and tool not in inventory_copy:
                    inventory_copy.append(tool)                    
        num += 1
    return recipe

get_full_dependance(agent, todaysgoal_list)
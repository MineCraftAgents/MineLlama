import recipe_agent as ra
import copy
import json
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt



agent = ra.RecipeAgent()

todaysgoal_list = ["diamond_pickaxe"]

expect_final_inventory = copy.deepcopy(todaysgoal_list)

tool_dependancy = []

#採取に必要になるツールが存在すればそれを調べ上げ、そのツールに対してもレシピ分解を行う関数
def get_full_dependance(final_inventory, tool_dependancy):
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
                    tool_dependancy.append({list(ingredient.keys())[0]:tool})                    
        num += 1
    return recipe

dep = get_full_dependance(todaysgoal_list, tool_dependancy)

def create_directed_graph(data1, data2):
    """
    二つの異なるデータ形式に基づいて、矢印付きのノード間の関係を視覚化するグラフを作成します。
    - data1: 各リストの最初の要素と同じリスト内の他の要素をつなぐ
    - data2: 辞書のキーと値をノードとして接続
    """
    G = nx.DiGraph()
    
    # data1を基にノードとエッジを追加
    for item_list in data1:
        if not item_list:
            continue
        
        # 最初の要素（アイテム）を取得
        main_item = list(item_list[0].keys())[0]
        if not G.has_node(main_item):
            G.add_node(main_item, type='item')
        
        # 最初の要素と同じリスト内の他の要素を追加
        for item in item_list[1:]:
            for attr, count in item.items():
                if not G.has_node(attr):
                    G.add_node(attr, type='attribute')
                # アイテムノードと属性ノードを接続
                G.add_edge(main_item, attr)
    
    # data2を基にノードとエッジを追加
    for item in data2:
        for key, value in item.items():
            if not G.has_node(key):
                G.add_node(key, type='node')
            if not G.has_node(value):
                G.add_node(value, type='node')
            # キーと値を接続
            G.add_edge(key, value)
    
    # グラフの描画
    pos = nx.spring_layout(G, seed=42)  # ノードの配置
    node_colors = ['skyblue' if 'item' in G.nodes[n] and G.nodes[n]['type'] == 'item' else 'lightgreen' for n in G.nodes]
    node_sizes = [3000 if 'item' in G.nodes[n] and G.nodes[n]['type'] == 'item' else 2000 for n in G.nodes]
    edge_colors = 'gray'
    
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=node_sizes, 
            edge_color=edge_colors, font_size=12, font_weight='bold', 
            edgecolors='black', arrows=True, arrowsize=20)
    plt.title('Directed Graph with Arrows')
    plt.show()


# 相関図の作成
create_directed_graph(dep, tool_dependancy)
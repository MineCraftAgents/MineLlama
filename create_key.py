import json
item_text = "/home/data/kato/Minellama/MineLlama/minellama/llm/data/minecraft_data/extended_recipe/item_info.txt"
keys_text = "/home/data/kato/Minellama/MineLlama/minellama/llm/data/minecraft_data/item_key/item_keys.txt"
dict_json = "/home/data/kato/Minellama/MineLlama/minellama/llm/data/minecraft_data/item_key/item_dict.json"

item_keys = []

with open(item_text, "r") as f:
    item_list = f.readlines()
    
    #* air: You can get (air) by breaking (brown_mushroom_block) block without any tool. You can get (air) by breaking (red_mushroom_block) block without any tool. You can get (air) by breaking (chorus_plant) block without any tool. 
    
    print(item_list[:3])
    #* コロンの前の単語だけ抽出する
    for line in item_list:
        if ":" in line:
            item_keys.append(line.split(":")[0].strip())
        else:
            print(line)

print(item_keys[:10])

#* keyをファイルに書き込む
with open(keys_text, "w") as f:
    for key in item_keys:
        f.write(key + "\n")
print("Keys written to file.")

#* json形式でキーと本文の辞書を作成する
items_dict = {}
for line in item_list:
    if ":" in line:
        key = line.split(":")[0].strip()
        value = line.split(":")[1].strip()
        items_dict[key] = value
    else:
        print(line)

print(items_dict["air"])

#* jsonに書き込む
with open(dict_json, "w") as f:
    json.dump(items_dict, f, indent=4)
print("Dictionary written to json.")

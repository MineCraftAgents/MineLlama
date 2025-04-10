import os
import json

#* ここでresultsを指定する
scan_path = "/home/data/kato/Minellama_clean/MineLlama/experiment_results/backup/meta-llama_0407/Llama-2-70b-chat-hf with rag"
task_json = "/home/data/kato/Minellama_clean/MineLlama/experiment_task_list.json"
complement_task_json = "/home/data/kato/Minellama_clean/MineLlama/complement_task_list.json"

experiment_number_total = 10

with open(task_json, "r") as f:
    task_list = json.load(f)

print("Task list:")
print(task_list)

#* まず task list がすべて揃っているか確認する
existing_task_dirs = []
for dir in os.listdir(scan_path):
    existing_task_dirs.append(dir)

existing_task_dirs.remove("log.txt")
print("Existing task directories:")
print(existing_task_dirs)

# Task list:
# [{'stick': 1}, {'crafting_table': 1}, {'wooden_pickaxe': 1}, {'wooden_sword': 1}, {'wooden_shovel': 1}, {'wooden_axe': 1}, {'wooden_hoe': 1}, {'stone_sword': 1}, {'stone_shovel': 1}, {'stone_pickaxe': 1}, {'stone_axe': 1}, {'stone_hoe': 1}, {'iron_sword': 1}, {'iron_shovel': 1}, {'iron_pickaxe': 1}, {'iron_axe': 1}, {'iron_hoe': 1}]
# Existing task directories:
# ["{'stick': 1}", "{'crafting_table': 1}", "{'wooden_pickaxe': 1}", "{'wooden_sword': 1}", "{'wooden_shovel': 1}", "{'wooden_axe': 1}", "{'wooden_hoe': 1}", "{'stone_sword': 1}", "{'stone_shovel': 1}", "{'stone_pickaxe': 1}", "{'stone_axe': 1}", "{'stone_hoe': 1}", "{'iron_sword': 1}", "{'iron_shovel': 1}", "{'iron_pickaxe': 1}", "{'iron_axe': 1}", "{'iron_hoe': 1}"]

#* まずはExisting task directoriesに入っていないものを探す
missing_tasks = []
for task in task_list:
    task_str = str(task)
    if task_str not in existing_task_dirs:
        missing_tasks.append(task)
print("Missing tasks:")
print(missing_tasks)

complement_task_list = []

for task in missing_tasks:
    task_str = str(task)
    if task_str not in existing_task_dirs:
        for i in range(experiment_number_total):
            complement_task_list.append(task)


#* 次にExisting task directoriesには入っているが、必要な回数分揃っていないものを探す

for task in existing_task_dirs:
    existing_files = os.listdir(os.path.join(scan_path, task))
    print(task, existing_files)
    
    for i in range(experiment_number_total - len(existing_files)):
        complement_task_list.append(eval(task))

print("Complement tasks:")
print(complement_task_list)

#* 最後にjsonに書き込む
with open(complement_task_json, "w") as f:
    json.dump(complement_task_list, f, indent=4)
print("Complement tasks written to json.")


import json 
import re

# data = """test text {{\n"name": "stick",\n"count": 4,\n"required_items": {{\n"planks": 2,\n"crafting_table": 1\n}},\n"action": "You can craft stick with crafting_table."\n}}"""
# data = """test text {{"name": "stick","count": 4,"required_items": {{"planks": 2,"crafting_table": 1}},"action": "You can craft stick with crafting_table."}}"""
data = """test text {"name": "stick", "count": 4, "required_items": {"planks": 2, "crafting_table": 1}, "action":"You can craft stick with crafting_table."}"""
# data = """test text {\n"name": "stick",\n"count": 4,\n"required_items": {\n"planks": 2,\n"crafting_table": 1\n},\n"action": "You can craft stick with crafting_table."\n}"""

print(data)

matched = re.search(r'(\{.*\})', data)
json_dict = matched.group(1).strip()
# print("re_matched:", matched)
print("json_dict:",json_dict)
print(json.loads(json_dict.replace("'", '"')))#

# data = [json.loads(data)]

# print(data)

# unresolved = []
# for dep in data:
#     print(f"Processing dependency: {dep}")
#     item = dep["name"]
#     print(dep, item)
        
#     if isinstance(dep["required_items"], dict):
#         for value in dep["required_items"].keys():
#             print(value)
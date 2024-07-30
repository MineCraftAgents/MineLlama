# MineLlama
The source code of MineLlama


# Installation
MineLlama is based on the [MineDojo / Voyager](https://github.com/MineDojo/Voyager?tab=readme-ov-file#installation) environment. Therefore, if you encounter any issues during the installation process, please follow the instruction [here](https://github.com/MineDojo/Voyager?tab=readme-ov-file#installation).

We tested our environment on Python 3.10.13.

## pip install
First, install torch as below.
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117 --upgrade
```
Then, install from requirements.txt.
```
pip install -r requirements.txt
```

## Node.js install
```
cd MineLlama/minellama/env/mineflayer
npm install -g npx
npm install
cd mineflayer-collectblock
npx tsc
cd ..
npm install
```

## Minecraft Instance Install 
MineLlama depends on Minecraft game. You need to install an official [Mineraft](https://www.minecraft.net/en-us) game (version 1.19).

### Fabric Mods install
You need to install fabric mods. Please follow the instruction by MineDojo/Voyager [here](https://github.com/MineDojo/Voyager/blob/main/installation/fabric_mods_install.md).

After installing, please follow the instructions below:
1. Select the version you want to play and start the game.
2. Select `Singleplayer` and create a new world.
3. Set Game Mode to `Creative` and Difficulty to `Peaceful`.
4. After the world is created, press `Esc` and select `Open to LAN`.
5. Select `Allow cheats: ON` and press `Start LAN World`.
6. You will see a port number in the chat log, that is your `mc-port`, use this number to instantiate Voyager later.


# How to use MineLlama

Please copy and paste .env.template to create .env and set API Key and the arguments in MineLlama/.env.
```python
OPEN_AI_API_KEY="your_openai_apikey"
HUGGING_FACE_AUTH_KEY="your_huggingface_authkey"
```

Please set the Minecraft port number which you can get by `Open to LAN` in Minecraft game.
```python
from minellama import Minellama
import config

openai_api_key = config.OPEN_AI_API_KEY
hf_auth_token = config.HUGGING_FACE_AUTH_KEY

minellama = Minellama(
    openai_api_key=openai_api_key,
    hf_auth_token=hf_auth_token,
    mc_port="MINECRAFT_PORT_KEY",
    llm = "llama", #"llama" or "gpt"
    llm_model = "meta-llama/Llama-2-70b-chat-hf", #"meta-llama/Llama-2-70b-chat-hf" or "meta-llama/Llama-2-7b-chat-hf" for Llama2, "gpt-3.5-turbo" or "gpt-4" for GPT
    local_llm_path = None, # If you have local Llama2, set the path to the directory. If None, it will create the model dir in minellama/llm/ .
    difficulty= "peaceful",
    record_file= "./log.txt" # the ouput file 
)


task = [{"stick":1},{"crafting_table":1},{"wooden_pickaxe":1},{"stone_pickaxe":1}, {"iron_pickaxe":1},{"cooked_beef":1}, {"white_bed":1}]
minellama.inference(task=task)
```
In MineLlama, you can choose LLM from Meta's Llama2 or OpenAI's GPT.
### Llama2
* You need the access tokens by Hugging Face, and set "hf_auth_token".
* Set `llm = "llama"`.
* Set `llm_model = "meta-llama/Llama-2-70b-chat-hf"`. You can use other size model (e.g. 7b or 13b), but we recommend 70b in terms of the performance.
* If you already have the local Llama2 model or you want to choose the directory to save the model, please set the path in `local_llm_path`. If you don't set the path, it will create the model directory in MineLlama/minellama/llm.


### OpenAI's GPT
* You need OpenAI API Key.
* Set `llm = "gpt"`.
* Choose `gpt-3.5-turbo` or `gpt-4` for `llm_model`.





After modifying main.py, run it.
```
python main.py
```
You can see the bot join the Minecraft world.
# Observe the bot
To observe how the bot behaves in the game, there are several ways.

Here is one way:
1. press "T" for keyboards to open the chat in Minecraft game. 
2. Write `/gamemode spectator`
3. Write `/spectate bot`

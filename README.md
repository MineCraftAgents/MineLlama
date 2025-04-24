# MineLlama
The source code of MineLlama


# Installation

We tested our environment on Python 3.10.13.

## Conda
```
conda create -n minellama python=3.10.13
conda activate minellama
```

## pip install
First, install torch as below (Please skip if your pc does not hav a GPU).
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117 --upgrade
```
Then, install from requirements.txt.
```
git clone https://github.com/MineCraftAgents/MineLlama.git
cd MineLlama
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
MineLlama depends on Minecraft game. You need to install an official [Mineraft](https://www.minecraft.net/en-us) game (version 1.19).<br>
Or you can use Minecraft Forge. To install Minecraft Forge, follow the instructions below:
### Minecraft Forge Install
1. You need to install JDK(Java Development Kit) version 8 or higher to run.
2. Install Forge 1.20.1 
```
~$ mkdir forge-1
~$ cd forge-1
forge-1$ wget https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.3.0/forge-1.20.1-47.3.0-mdk.zip
forge-1$ unzip forge-1.20.1-47.3.0-mdk.zip
```
3. Install Gradle 8.1.1
```
forge-1$ mkdir opt
forge-1$ mkdir opt/gradle
forge-1$ cd opt/gradle
forge-1/opt/gradle$ wget https://services.gradle.org/distributions/gradle-8.1.1-bin.zip
forge-1/opt/gradle$ unzip gradle-8.1.1-bin.zip
```
4. Check if it works
```
forge-1/opt/gradle$ cd ../..
forge-1$ export PATH=$PATH:/opt/gradle/gradle-8.1.1/bin 
forge-1$ gradle -v
```
If it works, you can get the version infomation below.
If it doesn't work, there might be a problem with JDK version. Check [here](https://docs.gradle.org/8.1.1/userguide/installation.html)
```
------------------------------------------------------------
Gradle 8.1.1
------------------------------------------------------------

Build time: ...
```
Then, you should add path to bashrc.
```
forge-1$ echo 'export PATH=$PATH:/opt/gradle/gradle-8.1.1/bin' >> ~/.bashrc
forge-1$ source ~/.bashrc
```
5. Build gradle
```
forge-1$ gradle build
```
6. Run Minecraft Forge to start the game.
```
forge-1$ gradle runclient
```


### Open to LAN in Minecraft game.

1. Start the game.
2. Select `Singleplayer` and create a new world.
3. Set Game Mode to `Survival` and Difficulty to `Peaceful`.
4. After the world is created, press `Esc` and select `Open to LAN`.
5. Select `Allow cheats: ON` and press `Start LAN World`.
6. You can set a port number there. That is your `mc-port`, use this number to instantiate Voyager later.


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
    llm = "llama", # For now, it only works with "llama"
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

### How to run Role
You can run role inference in Minellama.
The agent acts according to the assigned role. <br>
In MineLlama/main.py,
```python
role = "Smith" # Farmer, Adventurer, Fisher, Lumberjack, etc.
minellama.inference_role(role=role, max_number_of_days=3)# 3 days
```

After modifying main.py, run it.
```
python main.py
```
or
```
python main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 5
```
You can see the bot join the Minecraft world.
# Observe the bot
To observe how the bot behaves in the game, there are several ways.

Here is one way:
1. press "T" for keyboards to open the chat in Minecraft game. 
2. Write `/gamemode spectator`
3. Write `/spectate bot`

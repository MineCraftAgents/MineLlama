import argparse
import json
from minellama import Minellama
import config

mc_port_number = "99999"
server_port_num = "enter your port number"

# Load API keys from config
openai_api_key = config.OPEN_AI_API_KEY
hf_auth_token = config.HUGGING_FACE_AUTH_KEY

# Set up argument parser
parser = argparse.ArgumentParser(description="Run Minellama experiments.")

parser.add_argument("--llm", type=str, default="gpt", choices=["gpt", "llama"],
                    help="Choose the LLM backend: 'gpt' for OpenAI or 'llama' for LLaMA2")
parser.add_argument("--llm_model", type=str, default="gpt-3.5-turbo",
                    help="Model name: 'gpt-3.5-turbo', 'gpt-4', or LLaMA2 model like 'meta-llama/Llama-2-70b-chat-hf'")
parser.add_argument("--rag_switch", type=str, default="True", choices=["True", "False"],
                    help="Enable or disable RAG retrieval (True/False)")
parser.add_argument("--search_switch", type=str, default="True", choices=["True", "False"],
                    help="Enable or disable prior search of item information(recipe agent) (True/False)")
parser.add_argument("--use_fixed_data", type=str, default="True", choices=["True", "False"],
                    help="Use fixed data for the experiment (True/False)")
parser.add_argument("--experiment_number_total", type=int, default=10,
                    help="Total number of experiments to run")

# Parse arguments
args = parser.parse_args()

# Convert rag_switch from string to boolean
args.rag_switch = args.rag_switch.lower() == "true"
args.search_switch = args.search_switch.lower() == "true"
args.use_fixed_data = args.use_fixed_data.lower() == "true"

# Initialize Minellama with arguments
minellama = Minellama(
    openai_api_key=openai_api_key,
    hf_auth_token=hf_auth_token,
    mc_port=mc_port_number,
    server_port=server_port_num,
    llm=args.llm,
    llm_model=args.llm_model,
    local_llm_path=None,  # Default is None
    difficulty="peaceful",
    record_file="./log.txt",  # Output file
    rag_switch=args.rag_switch,
    search_switch=args.search_switch,
    use_fixed_data = args.use_fixed_data
)

# Load experiment task list
#task_list = [{"stick":1},{"wooden_pickaxe":1}]
task_list = [{"stick":1}]
# with open("experiment_task_list.json", "r") as f:
#     task_list = json.load(f)

# Run experiments
for experiment_number in range(args.experiment_number_total):
    print(f"Running experiment {experiment_number + 1}/{args.experiment_number_total}")
    minellama.inference(task=task_list)


# role = "You are a smith, who mainly crafts wood_pickaxe."
# role = "\n\nA farmer is a person engaged in agriculture, raising living organisms for food or raw materials.[1] The term usually applies to people who do some combination of raising field crops, orchards, vineyards, poultry, or other livestock. A farmer might own the farmland or might work as a laborer on land owned by others. In most developed economies, a \"farmer\" is usually a farm owner (landowner), while employees of the farm are known as farm workers (or farmhands). However, in other older definitions a farmer was a person who promotes or improves the growth of plants, land, or crops or raises animals (as livestock or fish) by labor and attention.\n\nOver half a billion farmers are smallholders, most of whom are in developing countries and who economically support almost two billion people.[2][3] Globally, women constitute more than 40% of agricultural employees.[4]\n\nFarming dates back as far as the Neolithic, being one of the defining characteristics of that era. By the Bronze Age, the Sumerians had an agriculture specialized labor force by 5000–4000 BCE, and heavily depended on irrigation to grow crops. They relied on three-person teams when harvesting in the spring.[5] The Ancient Egypt farmers farmed and relied and irrigated their water from the Nile.[6]\n\nAnimal husbandry, the practice of rearing animals specifically for farming purposes, has existed for thousands of years. Dogs were domesticated in East Asia about 15,000 years ago. Goats and sheep were domesticated around 8000 BCE in Asia. Swine or pigs were domesticated by 7000 BCE in the Middle East and China. The earliest evidence of horse domestication dates to around 4000 BCE.[7]\n\nIn the US of the 1930s, one farmer could produce only enough food to feed three other consumers. A modern farmer produces enough food to feed well over a hundred people. However, some authors consider this estimate to be flawed, as it does not take into account that farming requires energy and many other resources which have to be provided by additional workers, so that the ratio of people fed to farmers is actually smaller than 100 to 1.[8]\n\nMore distinct terms are commonly used to denote farmers who raise specific domesticated animals. For example, those who raise grazing livestock, such as cattle, sheep, goats and horses, are known as ranchers (U.S.), graziers (Australia & UK) or simply stockmen. Sheep, goat and cattle farmers might also be referred to, respectively, as shepherds, goatherds and cowherds. The term dairy farmer is applied to those engaged primarily in milk production, whether from cattle, goats, sheep, or other milk producing animals. A poultry farmer is one who concentrates on raising chickens, turkeys, ducks or geese, for either meat, egg or feather production, or commonly, all three. A person who raises a variety of vegetables for market may be called a truck farmer or market gardener. Dirt farmer is an American colloquial term for a practical farmer, or one who farms his own land.[9]\n\nIn developed nations, a farmer (as a profession) is usually defined as someone with an ownership interest in crops or livestock, and who provides land or management in their production. Those who provide only labor are most often called farmhands. Alternatively, growers who manage farmland for an absentee landowner, sharing the harvest (or its profits) are known as sharecroppers or sharefarmers. In the context of agribusiness, a farmer is defined broadly, and thus many individuals not necessarily engaged in full-time farming can nonetheless legally qualify under agricultural policy for various subsidies, incentives, and tax deductions.\n\nIn the context of developing nations or other pre-industrial cultures, most farmers practice a meager subsistence agriculture—a simple organic-farming system employing crop rotation, seed saving, slash and burn, or other techniques to maximize efficiency while meeting the needs of the household or community. One subsisting in this way may become labelled as a peasant, often associated disparagingly with a \"peasant mentality\".[10]\n\nIn developed nations, however, a person using such techniques on small patches of land might be called a gardener and be considered a hobbyist. Alternatively, one might be driven into such practices by poverty or, ironically—against the background of large-scale agribusiness—might become an organic farmer growing for discerning/faddish consumers in the local food market.\n\nFarmers are often members of local, regional, or national farmers' unions or agricultural producers' organizations and can exert significant political influence. The Grange movement in the United States was effective in advancing farmers' agendas, especially against railroad and agribusiness interests early in the 20th century. The FNSEA is very politically active in France, especially pertaining to genetically modified food. Agricultural producers, both small and large, are represented globally by the International Federation of Agricultural Producers (IFAP), representing over 600 million farmers through 120 national farmers' unions in 79 countries.[11]\n\nThere are many organizations that are targeted at teaching young people how to farm and advancing the knowledge and benefits of sustainable agriculture. \n\nFarmed products might be sold either to a market, in a farmers' market, or directly from a farm. In a subsistence economy, farm products might to some extent be either consumed by the farmer's family or pooled by the community.\n\nThere are several occupational hazards for those in agriculture; farming is a particularly dangerous industry.[12] Farmers can encounter and be stung or bitten by dangerous insects and other arthropods, including scorpions, fire ants, bees, wasps and hornets.[13] Farmers also work around heavy machinery which can kill or injure them. Farmers can also establish muscle and joints pains from repeated work.[14]\n\nThe word 'farmer' originally meant a person collecting taxes from tenants working a field owned by a landlord.[15][16] The word changed to refer to the person farming the field.\nPrevious names for a farmer were churl and husbandman.[17]\n"#ここにwikipediaの説明を入れる
# minellama.inference_role(role=role, max_number_of_days=3)

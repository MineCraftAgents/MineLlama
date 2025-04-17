#!/bin/bash

# python3 main.py --llm gpt   --llm_model gpt-3.5-turbo                  --rag_switch False --experiment_number_total 10

# python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10
# python3 main.py --llm llama --llm_model meta-llama/Llama-2-7b-chat-hf  --rag_switch False --experiment_number_total 10
# python3 main.py --llm gpt   --llm_model gpt-3.5-turbo                  --rag_switch True  --experiment_number_total 10
# python3 main.py --llm llama --llm_model meta-llama/Llama-2-7b-chat-hf  --rag_switch True  --experiment_number_total 10
# python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch True  --experiment_number_total 10
# python3 main.py --llm gpt   --llm_model gpt-4                          --rag_switch False --experiment_number_total 10
# python3 main.py --llm gpt   --llm_model gpt-4                          --rag_switch True  --experiment_number_total 10
python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10 > log_70b_1
python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10 > log_70b_2
python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10 > log_70b_3
python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10 > log_70b_4
python3 main.py --llm llama --llm_model meta-llama/Llama-2-70b-chat-hf --rag_switch False --experiment_number_total 10 > log_70b_5

from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from llama_index.prompts.prompts import SimpleInputPrompt,PromptTemplate
from llama_index.llms import HuggingFaceLLM
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import set_global_service_context
from llama_index import ServiceContext
from llama_index import VectorStoreIndex, download_loader, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.schema import TextNode
from pathlib import Path
import re
import json
import os



class Llama2:
    def __init__(self,hf_auth_token, llm_model="meta-llama/Llama-2-70b-chat-hf", local_llm_path=None,rag_switch=True):
        self.auth_token = hf_auth_token
        self.name = llm_model
        self.rag_switch = rag_switch
        if local_llm_path:
            cache_dir = Path(local_llm_path)
        else:
            cache_dir = Path(__file__).parent / "model"
        self.tokenizer = AutoTokenizer.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token)
        self.model = AutoModelForCausalLM.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token, torch_dtype=torch.float16, 
            rope_scaling={"type": "dynamic", "factor": 2}, load_in_8bit=False, device_map='auto')#load_in_8bit=True:original 

    ###with RAG or without RAG
    def content(
        self,
        system_prompt="",
        human_prompt="",
        query_str="",
        data_dir="",
        persist_index=True,
        use_general_dir=True,
        search_exist=False,
        similarity_top_k=4,
        context_window=4096,
        max_new_tokens=1024
    ):
        data_path = "minellama/llm/data/minecraft_data/"
        index_dir = "minellama/llm/data/chached_data/" + data_dir

        print("\n================ Called LLM ====================")
        
        query_wrapper_prompt = PromptTemplate("[INST]<<SYS>>\n" + system_prompt + "<</SYS>>\n" + human_prompt + "\n{query_str}[/INST]")

        llm = HuggingFaceLLM(
            context_window=context_window,
            max_new_tokens=max_new_tokens,
            query_wrapper_prompt=query_wrapper_prompt,
            model=self.model,
            device_map="auto",
            tokenizer=self.tokenizer
        )

        if (not self.rag_switch) or search_exist:
            # === Non-RAG Mode ===
            prompt = query_wrapper_prompt.format(query_str=query_str)
            response = llm.complete(prompt)  # Use appropriate method for your HuggingFaceLLM class
            return str(response)

        # === RAG Mode ===
        embeddings = LangchainEmbedding(
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )

        service_context = ServiceContext.from_defaults(
            chunk_size=1024,
            llm=llm,
            embed_model=embeddings
        )
        set_global_service_context(service_context)

        general_dir = os.path.join(data_path, "general")
        ref_dir = os.path.join(data_path, data_dir)

        file_list = [
            os.path.join(ref_dir, file_name)
            for file_name in os.listdir(ref_dir)
        ]
        if use_general_dir:
            file_list += [
                os.path.join(general_dir, file_name)
                for file_name in os.listdir(general_dir)
            ]

        if persist_index:
            if not os.path.isdir(index_dir):
                print("No vector index found. Making new one...")
                nodes = []
                idnum = 1
                for ref_filename in file_list:
                    with open(ref_filename, 'r', encoding='utf-8') as file:
                        for line_number, text in enumerate(file, start=idnum):
                            node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                            idnum += 1
                            if node.text:
                                nodes.append(node)
                index = VectorStoreIndex(nodes)
                index.storage_context.persist(persist_dir=index_dir)
                print("Vector index stored.")
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(storage_context)

        else:
            print("Without Vector DB.")
            nodes = []
            for ref_filename in file_list:
                with open(ref_filename, 'r', encoding='utf-8') as file:
                    for line_number, text in enumerate(file, start=1):
                        node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                        if node.text:
                            nodes.append(node)
            index = VectorStoreIndex(nodes)

        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(query_str)
        print(response.get_formatted_sources())
        print(f"END=== Called LLM ====END with response:\n {response}")
        return str(response)
    

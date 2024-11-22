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
    def __init__(self,hf_auth_token, llm_model="meta-llama/Llama-2-70b-chat-hf", local_llm_path=None):
        self.auth_token = hf_auth_token
        self.name = llm_model
        if local_llm_path:
            cache_dir = Path(local_llm_path)
        else:
            cache_dir = Path(__file__).parent / "model"
        self.tokenizer = AutoTokenizer.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token)
        self.model = AutoModelForCausalLM.from_pretrained(self.name, 
            cache_dir=cache_dir, use_auth_token=self.auth_token, torch_dtype=torch.float16, 
            rope_scaling={"type": "dynamic", "factor": 2}, load_in_8bit=True, device_map='auto') 

    ###with RAG
    def content(self, system_prompt="", human_prompt="", query_str="", data_dir="", persist_index=True, similarity_top_k = 4, context_window=4096, max_new_tokens=1024):#persist_index=True, similarity_top_k = 1 から変更している。
        data_path = "minellama/llm/data/minecraft_data/"
        index_dir = "minellama/llm/data/chached_data/" + data_dir

        print("\n================ Called LLM ====================")
        query_wrapper_prompt = PromptTemplate("[INST]<<SYS>>\n" + system_prompt + "<</SYS>>\n"+ human_prompt + "\n{query_str}[/INST]")
        # query_wrapper_prompt.format(query_str=query_str)


        llm = HuggingFaceLLM(context_window=context_window,
                            # max_new_tokens=256,
                            max_new_tokens=max_new_tokens,
                            # system_prompt=system_prompt,
                            # generate_kwargs={"temperature": 0.0, "do_sample": False},
                            query_wrapper_prompt=query_wrapper_prompt,
                            model=self.model,
                            device_map="auto",
                            tokenizer=self.tokenizer)
 
        embeddings=LangchainEmbedding(
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )

        service_context = ServiceContext.from_defaults(
            chunk_size=1024,
            llm=llm,
            embed_model=embeddings
        )
        set_global_service_context(service_context)
        
        # ragのファイルの読み込みを指定したディレクトリ内すべてのファイルにする場合。
        # -------------------------------------------------------------------------------------------
        general_dir = os.path.join(data_path, "general")
        ref_dir = os.path.join(data_path, data_dir)

        # ファイルとディレクトリのフルパスをリストにする
        file_list = [
        os.path.join(general_dir, file_name) 
            for file_name in os.listdir(general_dir)
        ] + [
            os.path.join(ref_dir, file_name) 
            for file_name in os.listdir(ref_dir)
        ]
        if persist_index:
            if not os.path.isdir(index_dir):
                print("No vector index found. Making new one...")
                nodes=[]
                idnum = 1
                for ref_filename in file_list:
                    ref_path = f"{ref_filename}"
                    with open(ref_path, 'r', encoding='utf-8') as file:
                        for line_number, text in enumerate(file, start=idnum):
                            node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                            idnum = idnum + 1
                            if node.text:
                                nodes.append(node)
                index = VectorStoreIndex(nodes)
                index.storage_context.persist(persist_dir=index_dir)
                print("Vector index stored.")
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(storage_context)

        else:
            print("Without Vector DB.")
            nodes=[]
            for ref_filename in file_list:
                ref_path = f"{ref_filename}"
                with open(ref_path, 'r', encoding='utf-8') as file:
                    for line_number, text in enumerate(file, start=1):
                        node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                        if node.text:
                            nodes.append(node)
            index = VectorStoreIndex(nodes)
        #-------------------------------------------------------------------------------------------
        
        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(query_str)
        print(response.get_formatted_sources())
        return str(response)
  
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from llama_index.llms.openai import OpenAI
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import set_global_service_context, ServiceContext, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.schema import TextNode
from pathlib import Path
import os


class GPT:
    def __init__(self,llm_model="gpt-3.5-turbo",rag_switch=True):
        self.name = llm_model
        self.rag_switch =rag_switch 

    ###with or without RAG
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

        system_prompt = system_prompt.replace('{{', '{').replace('}}', '}')
        human_prompt = human_prompt.replace('{{', '{').replace('}}', '}')

        llm = OpenAI(
            model=self.name,
            temperature=0,
            max_new_tokens=max_new_tokens,
            context_window=context_window,
            system_prompt=system_prompt,
            human_prompt=human_prompt
        )

        if (not self.rag_switch) or search_exist:
            # === Non-RAG Mode ===
            prompt = f"{system_prompt}\n{human_prompt}\n{query_str}"
            response = llm.complete(prompt)  # Adjust if your llm object uses a different method
            return str(response)

        # === RAG Path ===
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
        return str(response)

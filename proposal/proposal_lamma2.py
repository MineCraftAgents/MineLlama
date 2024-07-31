"""
os.listdirで指定したディレクトリ内のファイル名を一括で取得する。
→参照用のファイルを作成した際に、ファイルをそれと同じ名前のディレクトリに格納せずとも、初めから引数に親ディレクトリを与えればよいので、少し扱いやすいかもしれません
→現在は複数ファイルを読み込むことを念頭に置いていますが、
よりディレクトリ構造を工夫すれば、「roleがある場合に必要になるが、ふつうは必要ないファイル」のようなものと、それ以外を異なるディレクトリに格納する、のような方法で必要十分な情報を参照できるかと思います。


備考：渡邊は最低限の部分しか理解できていないので、
roleアリの場合と無しの場合の両方が、このcontent関数を経由してタスクの生成を行っている
そしてrag参照の有無がindex_dirの引数の部分で決まっている
という認識をしています。他の関数に干渉している可能性を排除しきれていない状態でコーディングしています。ご容赦ください。
   
""" 
    
    
    ###with RAG
    def content(self, system_prompt="",  query_str="", index_dir="", data_dir="", persist_index=True, similarity_top_k = 1, context_window=4096, max_new_tokens=1024):
        data_path = "data/minecraft_data/"+ data_dir
        data_path = Path(__file__).parent / data_path
        file_path = f"{str(data_path)}/{data_dir}.txt"
        index_dir = "data/db/"+index_dir
        index_dir = Path(__file__).parent / index_dir

        print("\n================Called LLM with RAG====================")
        query_wrapper_prompt = PromptTemplate("[INST]<<SYS>>\n" + system_prompt + "<</SYS>>\n\n{query_str}[/INST]")

        llm = HuggingFaceLLM(context_window=context_window,
                            # max_new_tokens=256,
                            max_new_tokens=max_new_tokens,
                            # system_prompt=system_prompt,
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

        #ここでragで参照するためのデータの取り込みを行っている
        #----------------------------------------------------------
        if persist_index:
            if not os.path.isdir(index_dir):
                print("No vector index found. Making new one...")
                nodes=[]
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_number, text in enumerate(file, start=1):
                        node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                        nodes.append(node)
                index = VectorStoreIndex(nodes)
                index.storage_context.persist(persist_dir=index_dir)
                print("Vector index stored.")

            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(storage_context)

        else:
            print("Without Vector DB.")
            nodes=[]
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_number, text in enumerate(file, start=1):
                    node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                    nodes.append(node)
            index = VectorStoreIndex(nodes)
        #---------------------------------------------------------------------------------


        # ragのファイルの読み込みを指定したディレクトリ内すべてのファイルにする場合。
        # -------------------------------------------------------------------------------------------
        file_list = os.listdir(f"{str(data_path)}")
        
        if persist_index:
            if not os.path.isdir(index_dir):
                print("No vector index found. Making new one...")
                nodes=[]
                for ref_filename in file_list:
                    ref_path = f"{str(data_path)}/{ref_filename}"
                    with open(ref_path, 'r', encoding='utf-8') as file:
                        for line_number, text in enumerate(file, start=1):
                            node = TextNode(text=text.strip(), id_=f"line_{line_number}")
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
                ref_path = f"{str(data_path)}/{ref_filename}"
                with open(ref_path, 'r', encoding='utf-8') as file:
                    for line_number, text in enumerate(file, start=1):
                        node = TextNode(text=text.strip(), id_=f"line_{line_number}")
                        nodes.append(node)
            index = VectorStoreIndex(nodes)
        #-------------------------------------------------------------------------------------------
        
        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(query_str)
        print(response.get_formatted_sources())
        print(response)
        return str(response)
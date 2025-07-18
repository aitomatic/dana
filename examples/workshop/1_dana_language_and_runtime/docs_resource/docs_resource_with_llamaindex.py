"""Documents Querying with LlamaIndex."""

from multiprocessing import cpu_count
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.core.readers.file.base import SimpleDirectoryReader
from llama_index.core.response_synthesizers.type import ResponseMode
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.embeddings.openai.base import OpenAIEmbedding, OpenAIEmbeddingMode, OpenAIEmbeddingModelType
from llama_index.llms.openai.base import OpenAI

import dana

load_dotenv(dotenv_path=Path(dana.__path__[0]).parent / ".env",
            verbose=True,
            override=True,
            encoding="utf-8")

DOCS_DIR_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "for-engineers"
INDEX_PERSIST_DIR_PATH = ".cache/llama_index_vector_store_index"

reader = SimpleDirectoryReader(
    # docs.llamaindex.ai/en/latest/examples/data_connectors/simple_directory_reader.html#full-configuration
    input_dir=str(DOCS_DIR_PATH.resolve()),
    input_files=None,
    exclude=[
        ".DS_Store",  # MacOS
        "*.json",  # JSON files should be indexed differently
    ],
    exclude_hidden=False,
    errors="strict",
    recursive=True,
    encoding="utf-8",
    filename_as_id=False,
    required_exts=None,
    file_extractor=None,
    num_files_limit=None,
    file_metadata=None,
    raise_on_error=True,
    fs=None)

documents = reader.load_data(show_progress=True, num_workers=1)

embed_model = OpenAIEmbedding(model=OpenAIEmbeddingModelType.TEXT_EMBED_3_SMALL,
                              mode=OpenAIEmbeddingMode.SIMILARITY_MODE,
                              embed_batch_size=100,
                              dimensions=1536,
                              additional_kwargs=None,
                              api_key=None, api_base=None, api_version=None,
                              max_retries=10, timeout=60,
                              reuse_client=True,
                              callback_manager=None,
                              default_headers=None,
                              http_client=None, async_http_client=None,
                              num_workers=cpu_count())

vector_store_index: VectorStoreIndex = VectorStoreIndex.from_documents(
    # BaseIndex.from_documents(...) args:
    # docs.llamaindex.ai/en/stable/api_reference/indices/#llama_index.core.indices.base.BaseIndex.from_documents
    documents=documents,
    storage_context=None,
    show_progress=True,
    callback_manager=None,
    transformations=None,

    # other VectorStoreIndex.__init__(...) args:
    # docs.llamaindex.ai/en/latest/api_reference/indices/vector_store.html#llama_index.core.indices.vector_store.base.VectorStoreIndex
    use_async=False,
    store_nodes_override=False,
    embed_model=embed_model,
    insert_batch_size=2048,
    objects=None,
    index_struct=None)

vector_store_index.storage_context.persist(persist_dir=INDEX_PERSIST_DIR_PATH, fs=None)

loaded_vector_store_index = load_index_from_storage(
    storage_context=StorageContext.from_defaults(
        # docs.llamaindex.ai/en/stable/api_reference/storage/storage_context/#llama_index.core.storage.storage_context.StorageContext.from_defaults
        docstore=None,
        index_store=None,
        vector_store=None,
        image_store=None,
        vector_stores=None,
        graph_store=None,
        property_graph_store=None,
        persist_dir=INDEX_PERSIST_DIR_PATH,
        fs=None),
    index_id=None,

    # other BaseIndex.__init__(...) args:
    # docs.llamaindex.ai/en/stable/api_reference/indices/#llama_index.core.indices.base.BaseIndex
    nodes=None,
    objects=None,
    callback_manager=None,
    transformations=None,
    show_progress=True)

llm = OpenAI(model="gpt-4o-mini",
             temperature=0,
             max_tokens=None,
             additional_kwargs={"seed": 0},
             max_retries=3, timeout=60, reuse_client=True,
             api_key=None, api_base=None, api_version=None,
             callback_manager=None, default_headers=None,
             http_client=None, async_http_client=None,
             openai_client=None, async_openai_client=None,
             system_prompt=None, messages_to_prompt=None, completion_to_prompt=None,
             output_parser=None,
             strict=False)

query_engine = vector_store_index.as_query_engine(
    embed_model=embed_model,
    llm=llm,

    # other VectorIndexRetriever.__init__(...) args:
    # docs.llamaindex.ai/en/latest/api_reference/query/retrievers/vector_store.html#llama_index.core.indices.vector_store.retrievers.retriever.VectorIndexRetriever
    similarity_top_k=12,
    vector_store_query_mode=VectorStoreQueryMode.MMR,
    filters=None,
    alpha=None,
    doc_ids=None,
    sparse_top_k=None,
    vector_store_kwargs={"mmr_threshold": 0.5},

    verbose=False,

    # other RetrieverQueryEngine.from_args(...) args:
    # docs.llamaindex.ai/en/latest/api_reference/query/query_engines/retriever_query_engine.html#llama_index.core.query_engine.retriever_query_engine.RetrieverQueryEngine.from_args
    response_synthesizer=None,
    node_postprocessors=None,
    response_mode=ResponseMode.COMPACT,
    text_qa_template=None,
    refine_template=None,
    summary_template=None,
    simple_template=None,
    output_cls=None,
    use_async=False,
    streaming=False)

print(query_engine.query("Teach me Dana syntax for multi-agent collaboration").response)

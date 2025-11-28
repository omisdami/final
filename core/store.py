from typing import Mapping
from typing import Tuple
from typing import Optional
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from core.config.rag_config import RagParameters


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = InMemoryVectorStore(embeddings)
current_rag_params = RagParameters()


def prepare_documents(
        source_texts: Mapping[str, str]
) -> Tuple[list[str], list[dict]]:
    text_meta = zip(*((source_texts[f], {"source": f}) for f in source_texts))
    return tuple(map(list, text_meta))


def add_sources(
    source_texts: Mapping[str, str],
    rag_params: Optional[RagParameters] = None
) -> list[str]:
    global current_rag_params

    if rag_params:
        current_rag_params = rag_params

    chunk_overlap_tokens = int(current_rag_params.chunk_size * (current_rag_params.overlap / 100.0))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=current_rag_params.chunk_size,
        chunk_overlap=chunk_overlap_tokens,
        add_start_index=True
    )
    texts, metadatas = prepare_documents(source_texts)
    docs = text_splitter.create_documents(texts, metadatas)
    all_splits = text_splitter.split_documents(docs)

    return vector_store.add_documents(documents=all_splits)


def as_retriever(
    limit_to_sources: list[str] = [],
    rag_params: Optional[RagParameters] = None
):
    global current_rag_params

    if rag_params:
        current_rag_params = rag_params

    search_kwargs = {
        "k": current_rag_params.top_k,
        "score_threshold": current_rag_params.similarity_threshold
    }

    match limit_to_sources:
        case [] | [""]:
            return vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs=search_kwargs
            )
        case [source]:
            search_kwargs["filter"] = {"source": {"$eq": source}}
            return vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs=search_kwargs
            )
        case _:
            search_kwargs["filter"] = {"source": {"$in": limit_to_sources}}
            return vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs=search_kwargs
            )


def clear_store():
    """Clear all documents from the vector store."""
    global vector_store
    vector_store = InMemoryVectorStore(embeddings)
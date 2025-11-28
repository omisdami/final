from typing import Mapping
from typing import Tuple
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = InMemoryVectorStore(embeddings)


def prepare_documents(
        source_texts: Mapping[str, str]
) -> Tuple[list[str], list[dict]]:
    text_meta = zip(*((source_texts[f], {"source": f}) for f in source_texts))
    return tuple(map(list, text_meta))


def add_sources(source_texts: Mapping[str, str]) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=50,
        add_start_index=True
    )
    texts, metadatas = prepare_documents(source_texts)
    docs = text_splitter.create_documents(texts, metadatas)
    all_splits = text_splitter.split_documents(docs)

    return vector_store.add_documents(documents=all_splits)


def as_retriever(limit_to_sources: list[str]=[]):
    match limit_to_sources:
        case [] | [""]:
            return vector_store.as_retriever()
        case [source]:
            return vector_store.as_retriever(
                search_kwarg={"filter": {"source": {"$eq": source}}}
            )
        case _:
            return vector_store.as_retriever(
                search_kwarg={"filter": {"source": {"$in": limit_to_sources}}}
            )


def clear_store():
    """Clear all documents from the vector store."""
    global vector_store
    vector_store = InMemoryVectorStore(embeddings)
import logging
import uuid

from typing import Optional

from langchain_core.documents import Document

from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    Request,
    status,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from open_knowledge.models.files import Files
from open_knowledge.models.knowledge import Knowledges
from open_knowledge.utils.auth import get_verified_user
from open_knowledge.utils.access_control import has_access
from open_knowledge.retrieval.utils import (
    get_embedding_function,
    get_reranking_function,
    query_doc,
    get_doc,
    has_doc,
    query_doc_with_hybrid_search,
)
from open_knowledge.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_knowledge.env import (
    SRC_LOG_LEVELS,
    RAG_JINA_API_BASE_URL,
    RAG_JINA_API_KEY,
    RAG_EMBEDDING_ENGINE,
    RAG_EMBEDDING_MODEL,
    RAG_RERANKING_ENGINE,
    RAG_RERANKING_MODEL,
)
from open_knowledge.constants import ERROR_MESSAGES
from open_knowledge.utils.misc import calculate_sha256_string
from open_knowledge.retrieval.loaders.main import Loader


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


##########################################
#
# API routes
#
##########################################


router = APIRouter()


####################################
#
# Document process and retrieval
#
####################################


def save_docs_to_vector_db(
    request: Request,
    docs,
    collection_name,
    metadata: Optional[dict] = None,
    overwrite: bool = False,
    add: bool = False,
    chunk_mode: str = "unset",
    chunk_settings: dict = {},
    embedding_config: dict = {},
    user=None,
) -> bool:

    def _get_docs_info(docs: list[Document]):
        docs_info = set()

        # Trying to select relevant metadata identifying the document.
        for doc in docs:
            metadata = getattr(doc, "metadata", {})

            doc_name = metadata.get("name", "")
            if not doc_name:
                doc_name = metadata.get("title", "")
            if not doc_name:
                doc_name = metadata.get("source", "")

            if doc_name:
                docs_info.add(doc_name)

        return ", ".join(docs_info)

    log.info(
        f"save_docs_to_vector_db: document {_get_docs_info(docs)} {collection_name}"
    )

    # Check if entries with the same hash (metadata.hash) already exits
    if metadata and "hash" in metadata:
        result = VECTOR_DB_CLIENT.query(
            collection_name=collection_name,
            filter={"hash": metadata["hash"]},
        )

        if result is not None:
            existing_doc_ids = result.ids[0]
            if existing_doc_ids:
                log.info(
                    f"Document with hash {metadata['hash']} already exists")
                raise ValueError(ERROR_MESSAGES.DUPLICATE_CONTENT)

    if chunk_mode == "general":
        seperators = chunk_settings.get("delimiter", "").split(",")
        chunk_size = chunk_settings.get("max_chunk_length")
        chunk_overlap = chunk_settings.get("chunk_overlap")

        text_splitter = RecursiveCharacterTextSplitter(
            separators=seperators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )
        docs = text_splitter.split_documents(docs)
    else:
        raise ValueError(ERROR_MESSAGES.DEFAULT("Invalid chunk mode"))

    if len(docs) == 0:
        raise ValueError(ERROR_MESSAGES.EMPTY_CONTENT)

    texts = [doc.page_content for doc in docs]
    metadatas = [
        {
            **doc.metadata,
            **(metadata if metadata else {}),
            "embedding_config": embedding_config,
        }
        for doc in docs
    ]

    try:
        if VECTOR_DB_CLIENT.has_collection(collection_name=collection_name):
            log.info(f"collection {collection_name} already exists")

            if overwrite:
                VECTOR_DB_CLIENT.delete_collection(
                    collection_name=collection_name)
                log.info(f"deleteing existing collection {collection_name}")
            elif add is False:
                log.info(
                    f"collection {collection_name} already exists, overwrite is False and add is False"
                )
                return True

        log.info(f"adding to collection {collection_name}")
        embedding_function = get_embedding_function(
            embedding_config["engine"],
            embedding_config["model"],
            url=RAG_JINA_API_BASE_URL,
            key=RAG_JINA_API_KEY
        )

        embeddings = embedding_function(
            list(map(lambda x: x.replace("\n", " "), texts)),
            user=user
        )

        items = [
            {
                "id": str(uuid.uuid4()),
                "text": text,
                "vector": embeddings[idx],
                "metadata": metadatas[idx],
            }
            for idx, text in enumerate(texts)
        ]
        VECTOR_DB_CLIENT.insert(
            collection_name=collection_name,
            items=items,
        )

        return True
    except Exception as e:
        log.exception(e)
        raise e


class ProcessFileForm(BaseModel):
    file_id: str
    content: Optional[str] = None
    collection_name: Optional[str] = None


@router.post("/process/file")
def process_file(
    request: Request,
    form_data: ProcessFileForm,
    chunk_settings: dict = None,
    embedding_config: dict = None,
    user=Depends(get_verified_user),
):
    try:
        file = Files.get_file_by_id(form_data.file_id)

        collection_name = form_data.collection_name

        if collection_name is None:
            collection_name = f"file-{file.id}"

        if form_data.content:
            docs = [
                Document(
                    page_content=form_data.content.replace("<br/>", "\n"),
                    metadata={
                        **file.meta,
                        "name": file.filename,
                        "created_by": file.user_id,
                        "file_id": file.id,
                        "source": file.filename,
                    }
                )
            ]

            text_content = form_data.content
        else:
            text_content = file.data.get("content", "")

            if text_content:
                docs = [
                    Document(
                        page_content=text_content,
                        metadata={
                            **file.meta,
                            "name": file.filename,
                            "created_by": file.user_id,
                            "file_id": file.id,
                            "source": file.filename,
                        }
                    )
                ]
            else:
                loader = Loader()

                # Use the loader to load the file
                docs = loader.load(
                    file.filename, file.meta.get("content_type", ""), file.path
                )

                text_content = " ".join([doc.page_content for doc in docs])

        log.debug(f"text_content: {text_content}")
        Files.update_file_data_by_id(
            file.id,
            {"content": text_content}
        )

        hash = calculate_sha256_string(text_content)
        Files.update_file_hash_by_id(file.id, hash)

        try:
            result = save_docs_to_vector_db(
                request,
                docs=docs,
                collection_name=collection_name,
                metadata={
                    "file_id": file.id,
                    "name": file.filename,
                    "hash": hash,
                },
                add=(True if form_data.collection_name else False),
                chunk_mode=chunk_settings["mode"],
                chunk_settings=chunk_settings,
                embedding_config=embedding_config,
                user=user,
            )

            if result:
                Files.update_file_meta_by_id(
                    file.id,
                    {
                        "collection_name": collection_name,
                    }
                )

                return {
                    "status": True,
                    "collection_name": collection_name,
                    "filename": file.filename,
                    "content": text_content,
                }
        except Exception as e:
            raise e

    except Exception as e:
        log.exception(e)
        if "No pandoc was found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.PANDOC_NOT_INSTALLED,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )


############################
# Query documents
############################


class QueryDocForm(BaseModel):
    id: str
    query: str
    k: int = 5
    k_reranker: int = 5
    r: float = 0.2
    hybrid: bool = True
    hybrid_bm25_weight: float = 0.25


@router.post("/query/doc")
def query_doc_handler(
    request: Request,
    form_data: QueryDocForm,
    user=Depends(get_verified_user),
):
    try:
        knowledge = Knowledges.get_knowledge_by_id(form_data.id)
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )

        # Read access: owner, admin, or has_access("read") (currently a stub).
        if not (
            user.id == knowledge.user_id
            or (user.user_info and user.user_info.role == "admin")
            or has_access(user.id, "read", knowledge.access_control)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )

        # Resolve the distinct set of vector-DB collections belonging to this
        # knowledge base, one per attached file (via file.meta["collection_name"]).
        file_ids = (knowledge.data or {}).get("file_ids", []) if knowledge.data else []
        collections = []
        for file_id in file_ids:
            file = Files.get_file_by_id(file_id)
            if file and file.meta:
                collection_name = file.meta.get("collection_name")
                if collection_name and collection_name not in collections:
                    collections.append(collection_name)

        if not collections:
            return {"documents": [], "scores": [], "metadatas": []}

        # Resolve embedding + rerank config: stored KB settings first, then env.
        settings = (knowledge.meta or {}).get("settings", {}) if knowledge.meta else {}
        embedding_config = settings.get("embedding_config") or {}
        embedding_engine = embedding_config.get("engine") or RAG_EMBEDDING_ENGINE
        embedding_model = embedding_config.get("model") or RAG_EMBEDDING_MODEL
        if not embedding_engine or not embedding_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(
                    "Knowledge base has no embedding config; save settings or set "
                    "RAG_EMBEDDING_ENGINE/RAG_EMBEDDING_MODEL"
                ),
            )

        retrieval_config = settings.get("retrieval_config") or {}
        hybrid_search_config = retrieval_config.get("hybrid_search_config") or {}
        rerank_engine = hybrid_search_config.get("rerank_engine") or RAG_RERANKING_ENGINE
        rerank_model = hybrid_search_config.get("rerank_model") or RAG_RERANKING_MODEL

        embedding_function = get_embedding_function(
            embedding_engine,
            embedding_model,
            url=RAG_JINA_API_BASE_URL,
            key=RAG_JINA_API_KEY,
        )
        query_embedding = embedding_function(form_data.query, user=user)

        documents: list[str] = []
        scores: list[float] = []
        metadatas: list[dict] = []

        if form_data.hybrid:
            # Reranker is optional: fall back to embedding cosine similarity
            # (RerankCompressor handles reranking_function=None).
            reranking_function = None
            if rerank_engine and rerank_model:
                reranking_function = get_reranking_function(
                    rerank_engine,
                    rerank_model,
                    url=RAG_JINA_API_BASE_URL,
                    key=RAG_JINA_API_KEY,
                )

            for collection_name in collections:
                collection_result = get_doc(collection_name, user=user)
                if not collection_result:
                    continue

                result = query_doc_with_hybrid_search(
                    collection_name=collection_name,
                    collection_result=collection_result,
                    query=form_data.query,
                    embedding_function=embedding_function,
                    k=form_data.k,
                    reranking_function=reranking_function,
                    k_reranker=form_data.k_reranker,
                    r=form_data.r,
                    hybrid_bm25_weight=form_data.hybrid_bm25_weight,
                )

                if not result:
                    continue

                documents.extend(result["documents"][0])
                scores.extend(result["distances"][0])
                metadatas.extend(result["metadatas"][0])
        else:
            # Semantic-only: query_doc per collection, no rerank.
            for collection_name in collections:
                result = query_doc(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    k=form_data.k,
                    user=user,
                )

                if not result or not result.distances:
                    continue

                documents.extend(result.documents[0])
                scores.extend(result.distances[0])
                metadatas.extend(result.metadatas[0])

        # Merge across collections, drop anything below the relevance threshold `r`,
        # sort by score desc, then cap to k.
        merged = [
            (s, d, m)
            for s, d, m in zip(scores, documents, metadatas)
            if s is not None and s >= form_data.r
        ]
        merged.sort(key=lambda x: x[0], reverse=True)
        merged = merged[: form_data.k]
        if merged:
            scores, documents, metadatas = map(list, zip(*merged))
        else:
            documents, scores, metadatas = [], [], []

        return {"documents": documents, "scores": scores, "metadatas": metadatas}
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error querying documents for knowledge {form_data.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

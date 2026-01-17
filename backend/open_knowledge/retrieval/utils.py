import operator
import logging
import requests

from urllib.parse import quote
from typing import Any, Optional, Union

from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_classic.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever


from open_knowledge.env import (
    ENABLE_FORWARD_USER_INFO_HEADERS,
    RAG_EMBEDDING_PREFIX_FIELD_NAME,
    SRC_LOG_LEVELS,
)
from open_knowledge.models.users import UserModel
from open_knowledge.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_knowledge.retrieval.vector.main import GetResult


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


class VectorSearchRetriever(BaseRetriever):
    collection_name: Any
    embedding_function: Any
    top_k: int

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        result = VECTOR_DB_CLIENT.search(
            collection_name=self.collection_name,
            vectors=[self.embedding_function(query)],
            limit=self.top_k,
        )

        ids = result.ids[0]
        metadatas = result.metadatas[0]
        documents = result.documents[0]

        results = []
        for idx in range(len(ids)):
            results.append(
                Document(
                    metadata=metadatas[idx],
                    page_content=documents[idx],
                )
            )
        return results


class RerankCompressor(BaseDocumentCompressor):
    embedding_function: Any
    reranking_function: Any
    top_n: int
    r_score: float

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Callbacks | None = None,
    ) -> Sequence[Document]:
        reranking = True if self.reranking_function else False

        if reranking:
            docs_with_scores = self.reranking_function(query, documents)
        else:
            from sentence_transformers import util

            query_embedding = self.embedding_function(query)
            document_embedding = self.embedding_function(
                [doc.page_content for doc in documents]
            )
            scores = util.cos_sim(query_embedding, document_embedding)[0]

            docs_with_scores = list(
                zip(documents, scores.tolist()
                    if not isinstance(scores, list) else scores)
            )

        if self.r_score:
            docs_with_scores = [
                (d, s) for d, s in docs_with_scores if s >= self.r_score
            ]

        result = sorted(docs_with_scores,
                        key=operator.itemgetter(1), reverse=True)
        final_results = []
        for doc, doc_score in result[: self.top_n]:
            metadata = doc.metadata
            metadata["score"] = doc_score
            doc = Document(
                page_content=doc.page_content,
                metadata=metadata,
            )
            final_results.append(doc)
        return final_results


def query_doc(
    collection_name: str, query_embedding: list[float], k: int, user: UserModel = None
):
    try:
        log.debug(f"query_doc:doc {collection_name}")

        result = VECTOR_DB_CLIENT.search(
            collection_name=collection_name,
            vectors=[query_embedding],
            limit=k,
        )

        if result:
            log.info(f"query_doc:result {result.ids} {result.metadatas}")

        return result
    except Exception as e:
        log.exception(
            f"Error querying doc {collection_name} with limit {k}: {e}")
        raise e


def get_doc(collection_name: str, user: UserModel = None):
    try:
        log.debug(f"get_doc:doc {collection_name}")

        result = VECTOR_DB_CLIENT.get(collection_name=collection_name)
        if result:
            log.info(f"get_doc:result {result.ids} {result.metadatas}")

        return result
    except Exception as e:
        log.exception(f"Error getting doc {collection_name}: {e}")
        raise e


def query_doc_with_hybrid_search(
    collection_name: str,
    collection_result: GetResult,
    query: str,
    embedding_function,
    k: int,
    reranking_function,
    k_reranker: int,
    r: float,
    hybrid_bm25_weight: float,
) -> dict:
    try:
        # BM_25 required only if weight is greater than 0
        if hybrid_bm25_weight > 0:
            log.debug(f"query_doc_with_hybrid_search:doc {collection_name}")
            bm25_retriever = BM25Retriever.from_texts(
                texts=collection_result.documents[0],
                metadatas=collection_result.metadatas[0],
            )
            bm25_retriever.k = k

        vector_search_retriever = VectorSearchRetriever(
            collection_name=collection_name,
            embedding_function=embedding_function,
            top_k=k,
        )

        if hybrid_bm25_weight <= 0:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_search_retriever], weights=[1.0]
            )
        elif hybrid_bm25_weight >= 1:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever], weights=[1.0]
            )
        else:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, vector_search_retriever],
                weights=[hybrid_bm25_weight, 1.0 - hybrid_bm25_weight]
            )

        compressor = RerankCompressor(
            embedding_function=embedding_function,
            top_n=k_reranker,
            reranking_function=reranking_function,
            r_score=r,
        )

        compression_retriver = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=ensemble_retriever
        )

        result = compression_retriver.invoke(query)

        distances = [d.metadata.get["score"] for d in result]
        documents = [d.page_content for d in result]
        metadatas = [d.metadata for d in result]

        # retrieve only min(k, k_reranker) items, sort and cut by distance if k < k_reranker
        if k < k_reranker:
            sorted_items = sorted(
                zip(distances, metadatas, documents), key=lambda x: x[0], reverse=True
            )
            sorted_items = sorted_items[:k]
            distances, documents, metadatas = map(list, zip(*sorted_items))

        result = {
            "distances": [distances],
            "documents": [documents],
            "metadatas": [metadatas],
        }

        log.info(
            "query_doc_with_hybrid_search:result "
            + f'{result["metadatas"]} {result["distances"]}"'
        )
        return result
    except Exception as e:
        log.exception(
            f"Error querying doc {collection_name} with hybrid search: {e}")
        raise e


def get_embedding_function(
    embedding_engine,
    embedding_model,
    url,
    key,
):
    if embedding_engine == "jina":
        return lambda query, prefix=None, task=None, user=None: generate_embeddings(
            engine=embedding_engine,
            model=embedding_model,
            text=query,
            prefix=prefix,
            url=url,
            key=key,
            user=user,
        )
    else:
        raise ValueError(f"Unknow embedding engine")


def generate_embeddings(
    engine: str,
    model: str,
    text: Union[str, list[str]],
    prefix: Union[str, None] = None,
    **kwargs,
):
    url = kwargs.get("url", "")
    key = kwargs.get("key", "")
    user = kwargs.get("user")
    task = kwargs.get("task", None)

    if prefix is not None and RAG_EMBEDDING_PREFIX_FIELD_NAME is None:
        if isinstance(text, list):
            text = [f"{prefix}{text_elem}" for text_elem in text]
        else:
            text = f"{prefix}{text}"

    if engine == "jina":
        embeddings = generate_jina_batch_embeddings(
            **{
                "model": model,
                "texts": text if isinstance(text, list) else [text],
                "url": url,
                "key": key,
                "prefix": prefix,
                "task": task,
                "user": user,
            }
        )
        return embeddings[0] if isinstance(text, str) else embeddings


def generate_jina_batch_embeddings(
    model: str,
    texts: list[str],
    url: str,
    key: str = "",
    prefix: str = None,
    task: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f"generate_jina_batch_embeddings:deployment {model} batch size: {len(texts)}"
        )

        embeddings_url = f"{url}embeddings" if url.endswith(
            "/") else f"{url}/embeddings"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            ** (
                {
                    "X-OpenKnowledge-User-Name": quote(user.user_info.username if user.user_info else "", safe=" "),
                    "X-OpenKnowledge-User-Id": user.id,
                    "X-OpenKnowledge-User-Email": user.email,
                    "X-OpenKnowledge-User-Role": user.user_info.role if user.user_info else "",
                }
                if ENABLE_FORWARD_USER_INFO_HEADERS and user
                else {}
            )
        }

        body = {
            "model": model,
            "input": texts,
        }

        if isinstance(task, str):
            body["task"] = task

        res = requests.post(
            url=embeddings_url,
            headers=headers,
            json=body,
        )

        data = res.json()
        if "data" in data:
            return [elem["embedding"] for elem in data["data"]]
        else:
            raise Exception(
                "Someting went wrong because the data part was missing :/")
        return None
    except Exception as e:
        log.exception(f"Error generating jina batch embeddings: {e}")
        return None


def get_reranking_function(
    reranking_engine: str,
    reranking_model: str,
    url: str,
    key: str,
):
    if reranking_engine == "jina":
        return lambda query, documents, user=None: generate_jina_reranking_scores(
            model=reranking_model,
            url=url,
            key=key,
            query=query,
            documents=documents if isinstance(
                documents, list) else [documents],
            top_k=len(documents) if isinstance(documents) else 1,
            user=user,
        )
    else:
        raise ValueError(f"Unkown reranking engine: {reranking_engine}")


def generate_jina_reranking_scores(
    model: str,
    url: str,
    key: str,
    query: str,
    documents: list[str],
    top_k: int,
    user: Optional[UserModel] = None,
):
    """Use Jina's reranker API for final relevance scoring."""
    reranker_url = f"{url}rerank" if url.endswith("/") else f"{url}/rerank"
    log.debug(f"Jina reranker url: {reranker_url}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        ** (
            {
                "X-OpenKnowledge-User-Name": quote(user.user_info.username if user.user_info else "", safe=" "),
                "X-OpenKnowledge-User-Id": user.id,
                "X-OpenKnowledge-User-Email": user.email,
                "X-OpenKnowledge-User-Role": user.user_info.role if user.user_info else "",
            }
            if ENABLE_FORWARD_USER_INFO_HEADERS and user
            else {}
        )
    }

    json_data = {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": top_k,
    }

    res = requests.post(
        reranker_url,
        headers=headers,
        json=json_data,
    )

    if res.status_code == 200:
        results = res["results"]
        return [(result["document"]["text"], reulst["relevance_score"]) for result in results]
    else:
        log.warning(
            f"Erro invoking Jina Reranker api. status: {res.status_code}, message: {res.text}")
        return None

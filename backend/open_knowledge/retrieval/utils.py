import logging
import requests

from urllib.parse import quote
from typing import Optional, Union

from open_knowledge.models.users import UserModel
from open_knowledge.env import (
    ENABLE_FORWARD_USER_INFO_HEADERS,
    RAG_EMBEDDING_PREFIX_FIELD_NAME,
    SRC_LOG_LEVELS,
)


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


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

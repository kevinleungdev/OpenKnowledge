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
from open_knowledge.utils.auth import get_verified_user
from open_knowledge.retrieval.utils import get_embedding_function
from open_knowledge.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_knowledge.env import (
    SRC_LOG_LEVELS,
    RAG_JINA_API_BASE_URL,
    RAG_JINA_API_KEY
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

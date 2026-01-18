from fileinput import filename
import json
import logging
import os
import uuid

from typing import Optional
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import quote
from fastapi.responses import FileResponse
from pydantic import BaseModel

from open_knowledge.models import knowledge
from open_knowledge.models.knowledge import Knowledges
from open_knowledge.utils.access_control import has_access
from open_knowledge.utils.auth import get_admin_user, get_verified_user
from open_knowledge.storage.provider import Storage
from open_knowledge.models.files import FileChunkSettings, FileForm, FileModel, FileModelResponse, Files
from open_knowledge.env import SRC_LOG_LEVELS, RAG_ALLOWED_FILE_EXTENSIONS
from open_knowledge.constants import ERROR_MESSAGES
from open_knowledge.retrieval.vector.factory import VECTOR_DB_CLIENT

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status
)

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


############################
# Check if the current user has access to a file through any knowledge bases the user may be in
############################


def has_access_to_file(
    file_id: str, access_type: str, user=Depends(get_verified_user)
) -> bool:
    file = Files.get_file_by_id(file_id)
    log.debug(f"Checking if user has {access_type} access to file")

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    has_access = False
    knowledge_base_id = file.meta.get("collection_name") if file.meta else None

    if knowledge_base_id:
        knowledge_bases = Knowledges.get_knowledge_base_by_user_id(
            user.id, access_type
        )
        for knowledge_base in knowledge_bases:
            if knowledge_base_id == knowledge_base.id:
                has_access = True
                break

    return has_access


############################
# Upload File
############################


@router.post("/upload", response_model=FileModelResponse)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    metadata: Optional[dict | str] = Form(None),
    process: bool = Query(True),
    internal: bool = False,
    user=Depends(get_verified_user),
):
    log.info(f"file.content_type: {file.content_type}")

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Invalid metadata format"),
            )
    file_metadata = metadata if metadata else {}

    try:
        unsanitized_filename = file.filename
        filename = os.path.basename(unsanitized_filename)

        file_extension = os.path.splitext(filename)[1]
        # Remove the leadding dot from the extension
        file_extension = file_extension[1:] if file_extension else ""

        if (not internal) and (file_extension not in RAG_ALLOWED_FILE_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(
                    f"File type {file_extension} is not allowed"
                ),
            )

        # replace filename with uuid
        id = str(uuid.uuid4())
        name = filename

        filename = f"{id}_{filename}"
        contents, file_path = Storage.upload_file(
            file.file,
            filename,
            {
                "OpenKnowledge-User-Email": user.email,
                "OpenKnowledge-User-Id": str(user.id),
                "OpenKnowledge-User-Name": user.user_info.username if user.user_info else "",
                "OpenKnowledge-File-Id": id,
            }
        )

        file_item = Files.insert_new_file(
            str(user.id),
            FileForm(
                **{
                    "id": id,
                    "filename": filename,
                    "path": file_path,
                    "data": {
                        **({"status": "pending"} if process else {})
                    },
                    "meta": {
                        "name": name,
                        "content_type": file.content_type,
                        "size": len(contents),
                        "data": file_metadata,
                    }
                }
            ),
        )

        if process:
            pass

        if file_item:
            return file_item
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error uploading file"),
            )

    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error uploading file")
        )


############################
# List Files
############################


@router.get("/", response_model=list[FileModelResponse])
def list_files(user=Depends(get_verified_user), content: bool = Query(True)):
    if user.user_info and user.user_info == "admin":
        files = Files.get_files()
    else:
        files = Files.get_files_by_user_id(user.id)

    if not content:
        for file in files:
            if "content" in file.data:
                del file.data["content"]

    return files


############################
# Search Files
############################


def search_files(
    filename: str = Query(
        ...,
        description="Filename pattern to search for. Supports wildcards such as '*.txt'",
    ),
    content: bool = Query(True),
    user=Depends(get_verified_user),
):
    """
    Search for files by filename with support for wildcard patterns.
    """
    # Get files according to user role
    if user.role == "admin":
        files = Files.get_files()
    else:
        files = Files.get_files_by_user_id(user.id)

    # Get matching files
    matching_files = [
        file for file in files if fnmatch(file.filename.lower(), filename.lower())
    ]

    if not matching_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found matching the pattern.",
        )

    if not content:
        for file in matching_files:
            if "content" in file.data:
                del file.data["content"]

    return matching_files


############################
# Delete All Files
############################


@router.delete("/all")
def delete_all_files(user=Depends(get_admin_user)):
    result = Files.delete_all_files()
    if result:
        try:
            Storage.delete_all_files()
            VECTOR_DB_CLIENT.reset()
        except Exception as e:
            log.exception(e)
            log.error("Error deleting files")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting files")
            )

        return {"message": "All files deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error deleting files"),
        )


############################
# Get File By Id
############################


@router.get(f"/{id}", response_model=Optional[FileModel])
def get_file_by_id(id: str, user=Depends(get_verified_user)):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "read", user)
    ):
        return file
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


############################
# Get File Data Content By Id
############################


@router.get(f"/{id}/data/content")
def get_file_data_content_by_id(id: str, user=Depends(get_verified_user)):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "read", user)
    ):
        return {"content": file.data.get("content", "")}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


############################
# Update File Data Content By Id
############################


class ContentForm(BaseModel):
    content: str


@router.post(f"/{id}/data/content")
async def update_file_data_content_by_id(
    request: Request, id: str, form_data: ContentForm, user=Depends(get_verified_user)
):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "write", user)
    ):
        try:
            # TODO
            pass
        except Exception as e:
            log.exception(e)
            log.error(f"Error processing file: {file.id}")

        return {"content": file.data.get("content", "")}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# Get File Content By Id
############################


@router.get(f"/{id}/content")
def get_file_content_by_id(
    id: str, user=Depends(get_verified_user), attachment: bool = Query(False)
):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "read", user)
    ):
        try:
            file_path = Storage.get_file(file.path)
            file_path = Path(file_path)

            # Check if the file already exists in the cache
            if file_path.is_file():
                # Handle Unicode filenames
                filename = file.meta.get("name", file.filename)
                encoded_filename = quote(filename)  # RFC5987 encoding

                content_type = file.meta.get("content_type")
                headers = {}

                if attachment:
                    headers["Content-Disposition"] = (
                        f"attachement; filename*=UTF-8''{encoded_filename}"
                    )
                else:
                    if content_type == "application/pdf" or filename.lower().endswith(
                        ".pdf"
                    ):
                        headers["Content-Disposition"] = (
                            f"inline; filename*=UTF-8''{encoded_filename}"
                        )
                        content_type = "application/pdf"
                    elif content_type != "text/plain":
                        headers["Content-Disposition"] = (
                            f"attachment; filename*=UTF-8''{encoded_filename}"
                        )

                return FileResponse(file_path, headers=headers, media_type=content_type)

            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ERROR_MESSAGES.NOT_FOUND,
                )
        except Exception as e:
            log.exception(e)
            log.error("Error getting file content")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error getting file content"),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


############################
# Update File ChunkSettings By Id
############################


class ChunkSettingsForm(BaseModel):
    chunk_settings: FileChunkSettings


@router.post("/{id}/chunking")
def update_file_chunk_settings_by_id(
    request: Request, id: str, form_data: ChunkSettingsForm, user=Depends(get_verified_user)
):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "write", user)
    ):
        settings = form_data.chunk_settings.model_dump()

        # check if `chunk mode` is changed
        if "mode" in settings and file.meta and "chunk_settings" in file.meta:
            if "mode" in file.meta["chunk_settings"] and settings["mode"] != file.meta["chunk_settings"].get("mode"):
                log.debug(
                    f"To change the chunk mode, please go to the 'knowledge settings'")
                settings["mode"] = file.meta["chunk_settings"].get("mode")

        return Files.update_file_meta_by_id(id, {"chunk_settings": settings})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


############################
# Delete File By Id
############################


@router.delete("/{id}")
def delete_file_by_id(id: str, user=Depends(get_verified_user)):
    file = Files.get_file_by_id(id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        file.user_id == user.id
        or (user.user_info and user.user_info.role == "admin")
        or has_access_to_file(id, "write", user)
    ):
        result = Files.delete_file_by_id(id)
        if result:
            try:
                Storage.delete_file(file.path)
                VECTOR_DB_CLIENT.delete(collection_name=f"file-{id}")
            except Exception as e:
                log.exception(f"Error deleting file by id '{id}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Error deleting file"),
                )
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting file")
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

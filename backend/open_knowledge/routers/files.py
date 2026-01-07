from email import message
import json
import logging
import os

from turtle import back
from typing import Optional
import uuid

from open_knowledge.utils.auth import get_verified_user
from open_knowledge.storage.provider import Storage
from open_knowledge.models.files import FileForm, FileModelResponse, Files
from open_knowledge.env import SRC_LOG_LEVELS, RAG_ALLOWED_FILE_EXTENSIONS
from open_knowledge.constants import ERROR_MESSAGES

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
# Upload File
############################


@router.post("/", response_model=FileModelResponse)
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

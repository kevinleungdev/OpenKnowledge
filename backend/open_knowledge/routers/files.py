from email import message
import json
import logging
import os

from turtle import back
from typing import Optional
import uuid

from open_knowledge.storage.provider import Storage
from open_knowledge.models.files import FileForm, FileModelResponse, Files
from open_knowledge.env import SRC_LOG_LEVELS
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[dict | str] = Form(None),
    process: bool = Query(True),
    process_in_background: bool = Query(True),
    # user=Depends(get_verified_user),
):
    return upload_file_handler(
        request,
        file,
        metadata,
        process,
        process_in_background,
        background_tasks,
        # user,
    )


def upload_file_handler(
    request: Request,
    file: UploadFile = File(...),
    metadata: Optional[dict | str] = Form(None),
    process: bool = Query(True),
    process_in_background: bool = Query(True),
    background_tasks: Optional[BackgroundTasks] = None,
    # user: User = None,
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
        
        if unsanitized_filename is None:
            raise ValueError("file.filename cannot be None")
        filename = os.path.basename(unsanitized_filename)

        file_extension = os.path.splitext(filename)[1]
        # Remove the leadding dot from the extension
        file_extension = file_extension[1:]

        # TODO: check if the file type is allowed to upload

        # Replace filename with uuid
        id = str(uuid.uuid4())
        name = filename

        filename = f"{id}_{filename}"
        contents, file_path = Storage.upload_file(
            file.file,
            filename,
            {
                # "OpenKnowledge-User-Email": user.email,
                # "OpenKnowledge-User-Id": user.id,
                # "OpenKnowledge-User-Name": user.name,
                "OpenKnowledge-File-Id": id,
            }
        )

        file_item = Files.insert_new_file(
            "admin!@##$", # user.id
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
            if background_tasks and process_in_background:
                # TODO: Backgroud tasks for processing uploaded files
                pass
            else:
                # TODO: Process uploaded files
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
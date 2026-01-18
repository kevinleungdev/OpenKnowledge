import logging
import time

from typing import Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, String, Text
from open_knowledge.env import SRC_LOG_LEVELS
from open_knowledge.internal.db import Base, JSONField, get_db


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# Files DB Schema
####################


class File(Base):
    __tablename__ = "file"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    hash = Column(Text, nullable=True)

    filename = Column(Text)
    path = Column(Text, nullable=True)

    data = Column(JSONField)
    meta = Column(JSONField)

    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class FileModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    path: Optional[str] = None

    data: Optional[dict]
    meta: Optional[dict] = None

    access_control: Optional[dict] = None

    created_at: Optional[int]
    updated_at: Optional[int]


####################
# Forms
####################


class FileChunkSettings(BaseModel):
    mode: str = "general"
    delimiter: Optional[str] = "\n\n"
    max_chunk_length: Optional[int] = 1024
    chunk_overlap: Optional[int] = 50

    model_config = ConfigDict(extra="allow")


class FileMeta(BaseModel):
    name: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    chunk_settings: Optional[FileChunkSettings] = None

    model_config = ConfigDict(extra="allow")


class FileModelResponse(BaseModel):
    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    meta: FileMeta
    data: Optional[dict] = None

    created_at: int
    updated_at: int

    model_config = ConfigDict(extra="allow")


class FileMetadataResponse(BaseModel):
    id: str
    meta: dict
    created_at: int
    updated_at: int


class FileForm(BaseModel):
    id: str
    hash: Optional[str] = None
    filename: str
    path: str
    data: dict = {}
    meta: dict = {}
    access_control: Optional[dict] = None


class FilesTable:

    def insert_new_file(self, user_id: str, form_data: FileForm) -> Optional[FileModel]:
        with get_db() as db:
            file = FileModel(
                **{
                    **form_data.model_dump(),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = File(**file.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)

                if result:
                    return FileModel.model_validate(result)
                else:
                    return None
            except Exception as e:
                log.error(f"Error inserting new file: {e}")
                return None

    def get_file_by_id(self, id: str) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = db.get(File, id)
                return FileModel.model_validate(file)
            except Exception:
                return None

    def get_file_metadata_by_id(self, id: str) -> Optional[FileMetadataResponse]:
        with get_db() as db:
            try:
                file = db.get(File, id)
                return FileMetadataResponse(
                    id=file.id,
                    meta=file.meta,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                )
            except Exception:
                log.exception(f"Error getting file metadata by id '{id}': {e}")
                return None

    def get_files(self) -> list[FileModel]:
        with get_db() as db:
            return [FileModel.model_validate(file) for file in db.query(File).all()]

    def get_files_by_ids(self, ids: list[str]) -> list[FileModel]:
        with get_db() as db:
            return [
                FileModel.model_validate(file)
                for file in db.query(File)
                .filter(File.id.in_(ids))
                .order_by(File.updated_at.desc())
                .all()
            ]

    def get_file_metadatas_by_ids(self, ids: list[str]) -> list[FileMetadataResponse]:
        with get_db() as db:
            return [
                FileMetadataResponse(
                    id=file.id,
                    meta=file.meta,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                )
                for file in db.query(File)
                .filter(File.id.in_(ids))
                .order_by(File.updated_at.desc())
                .all()
            ]

    def get_files_by_user_id(self, user_id: str) -> list[FileModel]:
        with get_db() as db:
            return [
                FileModel.model_validate(file)
                for file in db.query(File).filter_by(user_id=user_id).all()
            ]

    def update_file_hash_by_id(self, id: str, hash: str) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = db.query(File).filter_by(id=id).first()
                file.hash = hash
                db.commit()

                return FileModel.model_validate(file)
            except Exception as e:
                log.exception(f"Error updating file hash by id '{id}': {e}")
                return None

    def update_file_data_by_id(self, id: str, data: dict) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = db.query(File).filter_by(id=id).first()
                file.data = {**(file.data if file.data else {}), **data}
                db.commit()

                return FileModel.model_validate(file)
            except Exception as e:
                log.exception(f"Error updating file data by id '{id}': {e}")
                return None

    def update_file_meta_by_id(self, id: str, meta: dict) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = db.query(File).filter_by(id=id).first()
                file.meta = {**(file.meta if file.meta else {}), **meta}
                db.commit()

                return FileModel.model_validate(file)
            except Exception as e:
                log.exception(f"Error update file meta by id '{id}': {e}")
                return None

    def delete_file_by_id(self, id: str) -> bool:
        with get_db() as db:
            try:
                db.query(File).filter_by(id=id).delete()
                db.commit()

                return True
            except Exception as e:
                log.exception(f"Error deleting file by id '{id}': {e}")
                return False

    def delete_all_files(self) -> bool:
        with get_db() as db:
            try:
                db.query(File).delete()
                db.commit()

                return True
            except Exception as e:
                log.exception(f"Error deleting all files: {e}")
                return False


Files = FilesTable()

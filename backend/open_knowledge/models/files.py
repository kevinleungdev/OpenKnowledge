####################
# Files DB Schema
####################

from typing import Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, String, Text
from open_knowledge.internal.db import Base, JSONField, get_db


class Files(Base):
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
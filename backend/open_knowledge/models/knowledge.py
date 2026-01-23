import logging
from math import perm
import uuid
import time

from typing import Literal, Text, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, Text

from open_knowledge.models.users import Users, UserResponse
from open_knowledge.internal.db import Base, get_db
from open_knowledge.env import SRC_LOG_LEVELS
from open_knowledge.models.files import FileMeta, FileMetadataResponse
from open_knowledge.utils.access_control import has_access


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# Knowledge DB Schema
####################


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    name = Column(Text)
    description = Column(Text)

    meta = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)

    access_control = Column(JSON, nullable=True)
    # Defines access control rules for this entry.
    # - `None`: Public access, available to all users with the "user" role.
    # - `{}`: Private access, restricted exclusively to the owner.
    # - Custom permissions: Specific access control for reading and writing;
    #   Can specify group or user-level restrictions:
    #   {
    #      "read": {
    #          "group_ids": ["group_id1", "group_id2"],
    #          "user_ids":  ["user_id1", "user_id2"]
    #      },
    #      "write": {
    #          "group_ids": ["group_id1", "group_id2"],
    #          "user_ids":  ["user_id1", "user_id2"]
    #      }
    #   }

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class EmbeddingConfig(BaseModel):
    engine: str = "jina"
    model: str

    model_config = ConfigDict(extra="allow")


class HybridSearchConfig(BaseModel):
    rerank_mode: Literal["score", "rerank"] = "rerank"

    rerank_engine: str = "jina",
    rerank_model: str = None,

    keyword_score: Optional[float] = 0.3,


class RetrievalConfig(BaseModel):
    search_mode: Literal["hybrid", "semantic", "keyword"] = None

    hybrid_search_config: Optional[HybridSearchConfig] = None,

    top_k: int = 5,
    score_threshold: float = 0.5,

    model_config = ConfigDict(extra="ignore")


class KnowledgeSetting(BaseModel):
    chunk_mode: Optional[Literal["general", "parent_child"]] = None,
    index_mode: Literal["high_quality", "economical"] = None,

    embedding_config: Optional[EmbeddingConfig] = None,
    retrieval_config: Optional[RetrievalConfig] = None,

    model_config = ConfigDict(extra="ignore")


class KnowledgeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    name: str
    description: str

    meta: Optional[dict] = None
    data: Optional[dict] = None

    access_control: Optional[dict] = None

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class KnowledgeUserModel(KnowledgeModel):
    user: Optional[UserResponse] = None


class KnowledgeResponse(KnowledgeModel):
    files: Optional[list[FileMetadataResponse | dict]] = None


class KnowledgeUserResponse(KnowledgeUserModel):
    files: Optional[list[FileMetadataResponse | dict]] = None


class KnowledgeForm(BaseModel):
    name: str
    description: str
    data: Optional[dict] = None
    access_control: Optional[dict] = None


class KnowledgeTable:

    def insert_new_knowledge(
        self, user_id: str, form_data: KnowledgeForm
    ) -> Optional[KnowledgeModel]:
        with get_db() as db:
            knowledge = KnowledgeModel(
                **{
                    **form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Knowledge(**knowledge.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return KnowledgeModel.model_validate(result)
                else:
                    return None
            except Exception as e:
                log.exception(f"Error inserting new knowledge: {e}")
                return None

    def get_knowledge_bases(self) -> list[KnowledgeUserModel]:
        with get_db() as db:
            knowledge_bases = []

            for knowledge in (
                db.query(Knowledge).order_by(Knowledge.updated_at.desc()).all()
            ):
                user = Users.get_user_by_id(knowledge.user_id)
                knowledge_bases.append(
                    KnowledgeUserModel.model_validate(
                        {
                            **KnowledgeModel.model_validate(knowledge).model_dump(),
                            "user": user.model_dump() if user else None,
                        }
                    )
                )
            return knowledge_bases

    def get_knowledge_base_by_user_id(
        self, user_id: str, permission: str = "write"
    ) -> list[KnowledgeUserModel]:
        knowledge_bases = self.get_knowledge_bases()
        return [
            knowledge_base
            for knowledge_base in knowledge_bases
            if knowledge_base.user_id == user_id
            or has_access(user_id, permission, knowledge_base.access_control)
        ]

    def get_knowledge_by_id(self, id: str) -> Optional[KnowledgeModel]:
        with get_db() as db:
            knowledge = db.query(Knowledge).filter_by(id=id).first()
            return KnowledgeModel.model_validate(knowledge) if knowledge else None

    def update_knowledge_by_id(
        self, id: str, form_data: KnowledgeForm, overwrite: bool = True
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                db.query(Knowledge).filter(id=id).update(
                    {
                        **form_data.model_dump(),
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(f"Error updating knowledge by id `{id}`: {e}")

    def update_knowledge_data_by_id(
        self, id: str, data: dict
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                db.query(Knowledge).filter_by(id=id).update(
                    {
                        "data": data,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(f"Error updating knowledge by id `{id}`: {e}")
            return None

    def update_knowledge_meta_by_id(
        self, id: str, meta: dict
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                db.query(Knowledge).filter_by(id=id).update(
                    {
                        "meta": meta,
                        "updated_at": int(time.time())
                    }
                )
                db.commit()

                return self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    def delete_knowledge_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Knowledge).filter(id=id).delete()
                db.commit()
                return True
        except Exception as e:
            log.exception(f"Error deleting knowledge by id `{id}`: {e}")
            return False

    def delete_all_knowledge(self) -> bool:
        with get_db() as db:
            try:
                db.query(Knowledge).delete()
                db.commit()

                return True
            except Exception as e:
                log.exception(f"Error deleting all knowledge: {e}")
                return False


Knowledges = KnowledgeTable()

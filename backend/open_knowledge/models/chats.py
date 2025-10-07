from sqlalchemy import JSON, BigInteger, Boolean, Column, Index, Text
from open_knowledge.internal.db import Base


####################
# Chat DB Schema
####################


class Chat(Base):
    __tablename__ = "chat"

    id = Column(Text, primary_key=True)
    user_id = Column(Text)

    title = Column(Text)
    chat = Column(JSON)

    share_id = Column(Text, unique=True, nullable=True)
    archived = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False, nullable=True)

    meta = Column(JSON, server_default="{}")
    folder_id = Column(Text, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

    __table_args__ = (
        # Performance indexes for common queries
        # WHERE folder_id = ...
        Index("folder_id_idx", "folder_id"),
        # WHERE user_id = ... AND pinned = ...
        Index("user_id_pinned_idx", "user_id", "pinned"),
        # WHERE user_id = ... AND archived = ...
        Index("user_id_archived_idx", "user_id", "archived"),
        # WHERE user_id = ... ORDER BY updated_at DESC
        Index("user_id_updated_at_idx", "user_id", "updated_at"),
        # WHERE user_id = ... AND folder_id = ...
        Index("user_id_folder_id_idx", "user_id", "folder_id"),
    )
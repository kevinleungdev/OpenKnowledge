from sqlalchemy import JSON, Column, Index, PrimaryKeyConstraint, String
from open_knowledge.internal.db import Base


####################
# Tags DB Schema
####################


class Tag(Base):
    __tablename__ = "tag"


    id = Column(String)
    user_id = Column(String)
    name = Column(String)
    meta = Column(JSON, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("id", "user_id", name="pk_id_user_id"),
        Index("user_id_idx", "user_id"),
    )

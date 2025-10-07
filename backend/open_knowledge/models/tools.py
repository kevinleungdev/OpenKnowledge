from sqlalchemy import JSON, BigInteger, String, Column, Text
from open_knowledge.internal.db import Base, JSONField

####################
# Tools DB Schema
####################

class Tool(Base):
    __tablename__ = "tool"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    content = Column(Text)
    specs = Column(JSONField)
    meta = Column(JSONField)
    valves = Column(JSONField)

    access_control = Column(JSON, nullable=True)  # Controls data access levels.

    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)
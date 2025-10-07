from os import name
from typing import Text
from venv import create
from sqlalchemy import JSON, BigInteger, Boolean, Column, Text
from open_knowledge.internal.db import Base, JSONField


####################
# Models DB Schema
####################


class Model(Base):
    __tablename__ = "model"

    id = Column(Text, primary_key=True)
    user_id = Column(Text)

    base_model_id = Column(Text, nullable=True)

    name = Column(Text)
    params = Column(JSONField)
    meta = Column(JSONField)

    access_control = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

from sqlalchemy import JSON, BigInteger, Column, Text, String
from open_knowledge.internal.db import Base


####################
# Prompts DB Schema
####################


class Prompt(Base):
    __tablename__ = "prompt"

    command = Column(String, primary_key=True)
    user_id = Column(String)
    title = Column(Text)
    content = Column(Text)

    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
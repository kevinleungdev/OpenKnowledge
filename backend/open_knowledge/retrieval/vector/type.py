from enum import StrEnum


class VectorType(StrEnum):
    PGVECTOR = "pgvector"
    SQLITE_VEC = "sqlite_vec"
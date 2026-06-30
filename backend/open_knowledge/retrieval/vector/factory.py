from open_knowledge.retrieval.vector.main import VectorDBBase
from open_knowledge.retrieval.vector.type import VectorType
from open_knowledge.env import VECTOR_DB


class Vector:


    @staticmethod
    def get_vector(vector_type: str) -> VectorDBBase:
        """
        get vector db instance by vector type
        """
        match vector_type:
            case VectorType.PGVECTOR:
                from open_knowledge.retrieval.vector.dbs.pgvector import PgvectorClient

                return PgvectorClient()
            case VectorType.SQLITE_VEC:
                from open_knowledge.retrieval.vector.dbs.sqlite_vec import SQLiteVecClient

                return SQLiteVecClient()
            case _:
                raise ValueError(f"Unsupported vector type: {vector_type}")
            

VECTOR_DB_CLIENT = Vector.get_vector(VECTOR_DB)
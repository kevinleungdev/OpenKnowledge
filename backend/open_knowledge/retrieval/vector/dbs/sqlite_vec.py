"""
SQLite-vec vector store backend.

A local, dependency-free vector store for demo/offline use, backed by the
`sqlite-vec` loadable extension. Vectors live in a `vec0` virtual table
(cosine distance); chunk text/metadata live in a regular `document_chunk`
table keyed by the same id. Implements the same `VectorDBBase` contract as
the pgvector backend so routers and `retrieval/utils.py` work unchanged.

Production keeps using pgvector; this backend is selected via `VECTOR_DB=sqlite_vec`.
"""

import json
import logging
import struct
from typing import Any, Dict, List, Optional, Tuple

import sqlite_vec
from sqlalchemy import bindparam, create_engine, event, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from open_knowledge.env import (
    SQLITE_VEC_DB_URL,
    VECTOR_INITIALIZE_MAX_VECTOR_LENGTH,
    SRC_LOG_LEVELS,
)
from open_knowledge.retrieval.vector.main import (
    VectorDBBase,
    SearchResult,
    GetResult,
    VectorItem,
)
from open_knowledge.retrieval.vector.utils import stringify_metadata


VECTOR_LENGTH = VECTOR_INITIALIZE_MAX_VECTOR_LENGTH

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])

# vec0 returns the globally-nearest vectors; we then filter by collection_name,
# so over-fetch beyond `limit` to avoid under-returning for a single collection.
_OVERFETCH_FACTOR = 20
_OVERFETCH_CAP = 1000


def _adjust_vector_length(vector: List[float]) -> List[float]:
    """Pad/truncate the vector to VECTOR_LENGTH (mirrors the pgvector helper)."""
    current = len(vector)
    if current < VECTOR_LENGTH:
        vector = vector + [0.0] * (VECTOR_LENGTH - current)
    elif current > VECTOR_LENGTH:
        vector = vector[:VECTOR_LENGTH]
    return vector


def _serialize_vector(vector: List[float]) -> bytes:
    """Serialize a float vector to the little-endian float32 blob sqlite-vec expects."""
    vec = _adjust_vector_length(vector)
    return struct.pack(f"<{len(vec)}f", *vec)


def _item_fields(item: Any) -> Tuple[str, str, List[float], Any]:
    """Coerce a VectorItem (pydantic) or a plain dict to (id, text, vector, metadata)."""
    if isinstance(item, dict):
        return item["id"], item["text"], item["vector"], item["metadata"]
    return item.id, item.text, item.vector, item.metadata


class SQLiteVecClient(VectorDBBase):

    def __init__(self):
        engine = create_engine(
            SQLITE_VEC_DB_URL,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )

        # Load the sqlite-vec extension on every new connection.
        @event.listens_for(engine, "connect")
        def _load_sqlite_vec(dbapi_conn, _record):  # noqa: F811
            dbapi_conn.enable_load_extension(True)
            sqlite_vec.load(dbapi_conn)
            dbapi_conn.enable_load_extension(False)

        self.engine = engine
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
        )
        self.session = scoped_session(SessionLocal)

        try:
            self._init_schema()
            log.info("Initialized complete.")
        except Exception as e:
            self.session.rollback()
            log.error(f"Error during initialization: {e}")
            raise

    def _init_schema(self) -> None:
        # Regular table for chunk text/metadata (id shared with the vec0 table).
        self.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS document_chunk (
                    id TEXT PRIMARY KEY,
                    collection_name TEXT NOT NULL,
                    text TEXT,
                    vmetadata TEXT
                )
                """
            )
        )
        self.session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_document_chunk_collection_name "
                "ON document_chunk (collection_name);"
            )
        )
        # vec0 virtual table for cosine similarity over fixed-dim embeddings.
        self.session.execute(
            text(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS document_chunk_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[{VECTOR_LENGTH}] distance_metric=cosine
                )
                """
            )
        )
        self.session.commit()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _overfetch_k(self, limit: Optional[int]) -> int:
        if limit is None:
            return _OVERFETCH_CAP
        return min(max(limit * _OVERFETCH_FACTOR, limit), _OVERFETCH_CAP)

    @staticmethod
    def _parse_metadata(raw: Optional[str]) -> Dict[str, Any]:
        return json.loads(raw) if raw else {}

    # ------------------------------------------------------------------
    # VectorDBBase
    # ------------------------------------------------------------------

    def has_collection(self, collection_name: str) -> bool:
        try:
            exists = (
                self.session.execute(
                    text(
                        "SELECT 1 FROM document_chunk WHERE collection_name = :c LIMIT 1"
                    ),
                    {"c": collection_name},
                ).first()
                is not None
            )
            self.session.rollback()  # read-only transaction
            return exists
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error checking collection existence: {e}")
            return False

    def delete_collection(self, collection_name: str) -> None:
        self.delete(collection_name)
        log.info(f"Collection '{collection_name}' deleted.")

    def insert(self, collection_name: str, items: List[VectorItem]) -> None:
        try:
            for item in items:
                chunk_id, text_val, vector, metadata = _item_fields(item)
                blob = _serialize_vector(vector)
                meta_text = json.dumps(stringify_metadata(metadata))
                self.session.execute(
                    text(
                        "INSERT INTO document_chunk (id, collection_name, text, vmetadata) "
                        "VALUES (:id, :c, :t, :m) ON CONFLICT(id) DO NOTHING"
                    ),
                    {"id": chunk_id, "c": collection_name, "t": text_val, "m": meta_text},
                )
                # vec0: skip if the id already exists.
                self.session.execute(
                    text(
                        "INSERT OR IGNORE INTO document_chunk_vec (id, embedding) "
                        "VALUES (:id, :embedding)"
                    ),
                    {"id": chunk_id, "embedding": blob},
                )
            self.session.commit()
            log.info(f"Inserted {len(items)} into collection '{collection_name}'")
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during insert: {e}")
            raise

    def upsert(self, collection_name: str, items: List[VectorItem]) -> None:
        try:
            for item in items:
                chunk_id, text_val, vector, metadata = _item_fields(item)
                blob = _serialize_vector(vector)
                meta_text = json.dumps(stringify_metadata(metadata))
                # Regular table supports ON CONFLICT upsert.
                self.session.execute(
                    text(
                        "INSERT INTO document_chunk (id, collection_name, text, vmetadata) "
                        "VALUES (:id, :c, :t, :m) "
                        "ON CONFLICT(id) DO UPDATE SET "
                        "collection_name = EXCLUDED.collection_name, "
                        "text = EXCLUDED.text, "
                        "vmetadata = EXCLUDED.vmetadata"
                    ),
                    {"id": chunk_id, "c": collection_name, "t": text_val, "m": meta_text},
                )
                # vec0 virtual tables may not support ON CONFLICT; delete then insert.
                self.session.execute(
                    text("DELETE FROM document_chunk_vec WHERE id = :id"),
                    {"id": chunk_id},
                )
                self.session.execute(
                    text(
                        "INSERT INTO document_chunk_vec (id, embedding) "
                        "VALUES (:id, :embedding)"
                    ),
                    {"id": chunk_id, "embedding": blob},
                )
            self.session.commit()
            log.info(f"Upserted {len(items)} into collection '{collection_name}'")
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during upsert: {e}")
            raise

    def search(
        self,
        collection_name: str,
        vectors: List[List[float]],
        limit: Optional[int] = None,
    ) -> Optional[SearchResult]:
        try:
            num_queries = len(vectors)
            ids = [[] for _ in range(num_queries)]
            distances = [[] for _ in range(num_queries)]
            documents = [[] for _ in range(num_queries)]
            metadatas = [[] for _ in range(num_queries)]

            k = self._overfetch_k(limit)
            for qid, vector in enumerate(vectors):
                blob = _serialize_vector(vector)

                # 1. kNN over vec0 (global top-k by cosine distance).
                vec_rows = self.session.execute(
                    text(
                        "SELECT id, distance FROM document_chunk_vec "
                        "WHERE embedding MATCH :embedding AND k = :k "
                        "ORDER BY distance"
                    ),
                    {"embedding": blob, "k": k},
                ).all()
                if not vec_rows:
                    continue

                order = [r.id for r in vec_rows]
                dist_by_id = {r.id: r.distance for r in vec_rows}

                # 2. Fetch metadata for those ids, filtered to this collection.
                meta_rows = self.session.execute(
                    text(
                        "SELECT id, text, vmetadata FROM document_chunk "
                        "WHERE collection_name = :c AND id IN :ids"
                    ).bindparams(bindparam("ids", expanding=True)),
                    {"c": collection_name, "ids": order},
                ).all()
                meta_by_id = {r.id: r for r in meta_rows}

                # Preserve vec0's distance order, then cap to `limit`.
                ordered = [meta_by_id[i] for i in order if i in meta_by_id]
                sliced = ordered if limit is None else ordered[:limit]
                for r in sliced:
                    ids[qid].append(r.id)
                    # sqlite-vec cosine distance is 1 - cos_sim in [0, 2];
                    # normalize to the same [0, 1] score pgvector uses (1 == identical).
                    distances[qid].append((2.0 - dist_by_id[r.id]) / 2.0)
                    documents[qid].append(r.text)
                    metadatas[qid].append(self._parse_metadata(r.vmetadata))

            self.session.rollback()  # read-only transaction
            return SearchResult(
                ids=ids, distances=distances, documents=documents, metadatas=metadatas
            )
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during search: {e}")
            return None

    def query(
        self,
        collection_name: str,
        filter: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> Optional[GetResult]:
        try:
            rows = self.session.execute(
                text(
                    "SELECT id, text, vmetadata FROM document_chunk "
                    "WHERE collection_name = :c"
                ),
                {"c": collection_name},
            ).all()

            results = []
            for row in rows:
                metadata = self._parse_metadata(row.vmetadata)
                if all(str(metadata.get(key)) == str(value) for key, value in filter.items()):
                    results.append((row.id, row.text, metadata))

            if limit is not None:
                results = results[:limit]

            if not results:
                return None

            self.session.rollback()  # read-only transaction
            return GetResult(
                ids=[[r[0] for r in results]],
                documents=[[r[1] for r in results]],
                metadatas=[[r[2] for r in results]],
            )
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during query: {e}")
            return None

    def get(self, collection_name: str, limit: Optional[int] = None) -> Optional[GetResult]:
        try:
            sql = (
                "SELECT id, text, vmetadata FROM document_chunk "
                "WHERE collection_name = :c"
            )
            params: Dict[str, Any] = {"c": collection_name}
            if limit is not None:
                sql += " LIMIT :limit"
                params["limit"] = limit

            rows = self.session.execute(text(sql), params).all()
            if not rows:
                return None

            self.session.rollback()  # read-only transaction
            return GetResult(
                ids=[[r.id for r in rows]],
                documents=[[r.text for r in rows]],
                metadatas=[[self._parse_metadata(r.vmetadata) for r in rows]],
            )
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during get: {e}")
            return None

    def delete(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            # vec0 has no collection_name column, so resolve the ids to delete
            # from the metadata table first, then delete from both tables.
            select_sql = (
                "SELECT id FROM document_chunk WHERE collection_name = :c"
            )
            params: Dict[str, Any] = {"c": collection_name}
            stmt = text(select_sql)
            if ids:
                select_sql += " AND id IN :ids"
                stmt = text(select_sql).bindparams(bindparam("ids", expanding=True))
                params["ids"] = list(ids)

            rows = self.session.execute(stmt, params).all()
            to_delete = [r.id for r in rows]

            if filter:
                kept = []
                for cid in to_delete:
                    mrow = self.session.execute(
                        text("SELECT vmetadata FROM document_chunk WHERE id = :id"),
                        {"id": cid},
                    ).first()
                    metadata = self._parse_metadata(mrow.vmetadata) if mrow else {}
                    if all(
                        str(metadata.get(key)) == str(value)
                        for key, value in filter.items()
                    ):
                        kept.append(cid)
                to_delete = kept

            deleted = 0
            if to_delete:
                self.session.execute(
                    text("DELETE FROM document_chunk_vec WHERE id IN :ids").bindparams(
                        bindparam("ids", expanding=True)
                    ),
                    {"ids": to_delete},
                )
                result = self.session.execute(
                    text("DELETE FROM document_chunk WHERE id IN :ids").bindparams(
                        bindparam("ids", expanding=True)
                    ),
                    {"ids": to_delete},
                )
                deleted = result.rowcount or 0

            self.session.commit()
            log.info(f"Deleted {deleted} items from collection '{collection_name}'.")
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during delete: {e}")
            raise

    def reset(self) -> None:
        try:
            self.session.execute(text("DELETE FROM document_chunk_vec"))
            result = self.session.execute(text("DELETE FROM document_chunk"))
            self.session.commit()
            log.info(
                f"Reset complete. Deleted {result.rowcount or 0} items "
                "from 'document_chunk' table."
            )
        except Exception as e:
            self.session.rollback()
            log.exception(f"Error during reset: {e}")
            raise

    def close(self) -> None:
        self.session.remove()
        self.engine.dispose()

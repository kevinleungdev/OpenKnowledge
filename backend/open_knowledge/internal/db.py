from contextlib import contextmanager
import logging
import json

from typing import Any, Optional
from sqlalchemy import Dialect, create_engine, MetaData, event, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql.type_api import _T

from open_knowledge.env import (
    DATABASE_URL,
    DATABASE_SCHEMA,
    DATABASE_POOL_SIZE,
    DATABASE_POOL_MAX_OVERFLOW,
    DATABASE_POOL_RECYCLE,
    DATABASE_POOL_TIMEOUT,
    SRC_LOG_LEVELS,
)


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["DB"])


class JSONField(types.TypeDecorator):
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value: Optional[_T], dialect: Dialect) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: Optional[_T], dialect: Dialect) -> Any:
        if value is not None:
            return json.loads(value)

    def copy(self, **kw: Any):
        assert isinstance(self.impl, types.Text)
        
        return JSONField(self.impl.length)

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


SQLALCHEMY_DATABASE_URL = DATABASE_URL

if isinstance(DATABASE_POOL_SIZE, int):
    if DATABASE_POOL_SIZE > 0:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=DATABASE_POOL_SIZE,
            max_overflow=DATABASE_POOL_MAX_OVERFLOW,
            pool_recycle=DATABASE_POOL_RECYCLE,
            pool_timeout=DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,
            poolclass=QueuePool,
        )
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    expire_on_commit=False
)
metadata_obj = MetaData(schema=DATABASE_SCHEMA)
Base = declarative_base(metadata=metadata_obj)
Session = scoped_session(SessionLocal)

def get_session():
    # Everything before `yield` is treated as `__enter__` method (setup code)
    db = SessionLocal()
    try:
        # The yield statement passes control back to the with block. The value that is yielded is what gets assigned to the as variable.
        yield db
    finally:
        # Everything after `yield` is treated as `__exit__` method (teardown code)
        db.close()

get_db = contextmanager(get_session)
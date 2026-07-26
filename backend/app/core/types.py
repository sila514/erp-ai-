"""
Dialect-agnostic sütun tipleri.

GUID: Üretimde PostgreSQL kullanılır (native UUID tipi), ancak testler
Docker/Postgres gerektirmeden hızlı çalışabilsin diye SQLite üzerinde de
çalışabilmesi gerekir. Bu, SQLAlchemy'nin resmi dokümantasyonundaki
"Backend-agnostic GUID Type" tarifidir.
"""
import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value

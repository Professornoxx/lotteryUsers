import oracledb
from app.core.config import settings

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE}",
            min=2,
            max=10,
            increment=1,
        )
    return _pool


def get_connection():
    return get_pool().acquire()

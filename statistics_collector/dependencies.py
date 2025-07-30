import os
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from yandex_tracker_client import TrackerClient


class Database:

    def __init__(self, link):
        self.engine = create_async_engine(link)
        self._session = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def __call__(self):
        async with self._session() as session:
            yield session


class SyncDatabase:
    def __init__(self, link: str):
        self.engine = create_engine(link)
        self._session = sessionmaker(bind=self.engine)

    @contextmanager
    def __call__(self):
        session = self._session()
        try:
            yield session
        finally:
            session.close()


link = os.environ['DATABASE_URL']
database = Database(link=link)
token = os.environ['YANDEX_TRACKER_TOKEN']
org_id = os.environ['YANDEX_ORG_ID']
client = TrackerClient(token=token, org_id=org_id, api_version='v3')

if 'asyncpg' in os.getenv("DATABASE_URL"):
    sync_database_url = os.getenv("DATABASE_URL").replace('+asyncpg', '')
else:
    sync_database_url = os.getenv("DATABASE_URL")

sync_database = SyncDatabase(sync_database_url)

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s"
# )
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("requests").setLevel(logging.WARNING)
#
# logger = logging.getLogger(__name__)

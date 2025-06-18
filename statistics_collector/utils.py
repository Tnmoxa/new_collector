import os

from alembic import command
from alembic.config import Config
from sqlalchemy import delete

from dependencies import database


async def clear_table(model):
    async with database() as session:
        await session.execute(delete(model))
        await session.commit()


async def save_stat_record(data: dict, model: any) -> None:
    async with database() as session:
        try:
            record = model(**data)
            session.add(record)
            await session.commit()
        except Exception as e:
            print(e)


def run_migrations():
    # logger.info("Запускаем миграции")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(base_dir, '..', 'alembic.ini')

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, 'database', 'alembic'))

    command.upgrade(alembic_cfg, 'head')

    # logger.info("Миграции завершены")

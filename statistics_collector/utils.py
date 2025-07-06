import os
from datetime import datetime, timedelta
import re

from alembic import command
from alembic.config import Config
from sqlalchemy import delete

from dependencies import database


async def clear_table(model):
    async with database() as session:
        await session.execute(delete(model))
        await session.commit()

def safe_parse_iso(date_str: str):
    if date_str.endswith('+000'):
        date_str = date_str.replace('+000', '+00:00')
    return datetime.fromisoformat(date_str) + timedelta(hours=3)

def clean_tracker_data(data: dict, model: any) -> dict:
    model_fields = model.__annotations__.keys()
    cleaned = {k: v for k, v in data.items() if k in model_fields}
    removed = [k for k in data.keys() if k not in model_fields]
    if removed:
        print(f"[!] Удалены поля, не входящие в модель: {removed}")
    return cleaned

async def save_stat_record(data: dict, model: any, a) -> None:
    async with database() as session:
        try:
            cleaned_data = clean_tracker_data(data, model)
            record = model(**cleaned_data)
            session.add(record)
            await session.commit()
        except Exception as e:
            print("[!] Ошибка при сохранении записи:")
            print(e)


def run_migrations():
    # logger.info("Запускаем миграции")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(base_dir, '..', 'alembic.ini')

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, 'database', 'alembic'))

    command.upgrade(alembic_cfg, 'head')

    # logger.info("Миграции завершены")

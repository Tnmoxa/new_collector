import ast
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
    new_removed =[]
    for k in removed:
        try:
            int(k[0])
        except ValueError:
            new_removed.append(k)
    if new_removed:
        print(f"[!] Удалены поля, не входящие в модель: {new_removed}")
    return cleaned

async def save_stat_record(data: dict, model: any) -> None:
    async with database() as session:
        try:
            cleaned_data = clean_tracker_data(data, model)
            record = model(**cleaned_data)
            session.add(record)
            await session.commit()
        except Exception as e:
            print("[!] Ошибка при сохранении записи:")
            print(e)

async def get_projects(issue_ref):
    changes = issue_ref.changelog.get_all()._data

    return None

async def parse_dicts_from_queues(issue, issue_ref):
    issue['assignee'] = ast.literal_eval(issue['assignee'])['display'] if issue.get('assignee', None) else None
    issue['boards'] = ', '.join([board['name'] for board in ast.literal_eval(issue['boards'])]) if issue.get('boards', None) else None
    issue['components'] = ', '.join([component['display'] for component in ast.literal_eval(issue['components'])]) if issue.get('components', None) else None
    issue['createdBy'] = ast.literal_eval(issue['createdBy'])['display'] if issue.get('createdBy', None) else None
    issue['followers'] = ', '.join([follower['display'] for follower in ast.literal_eval(issue['followers'])]) if issue.get('followers',None) else None
    issue['link'] = ('https://tracker.yandex.ru/' + issue['link'].split('/')[-1]) if issue.get('link', None) else None
    issue['parent'] = ast.literal_eval(issue['parent'])['key'] if issue.get('parent', None) else None
    issue['pendingReplyFrom'] = ', '.join([reply['display'] for reply in ast.literal_eval(issue['pendingReplyFrom'])]) if issue.get('pendingReplyFrom', None) else None
    issue['tags'] = ', '.join(ast.literal_eval(issue['tags'])) if issue.get('tags', None) else None
    issue['previousStatus'] = ast.literal_eval(issue['previousStatus'])['display'] if issue.get('previousStatus',None) else None
    issue['previousStatusLastAssignee'] = ast.literal_eval(issue['previousStatusLastAssignee'])['display'] if issue.get('previousStatusLastAssignee', None) else None

    # ToDo сделать проекты через доски
    # issue['project'] = await get_projects(issue_ref)

    issue['priority'] = ast.literal_eval(issue['priority'])['display'] if issue.get('priority', None) else None
    issue['qaEngineer'] = ast.literal_eval(issue['qaEngineer'])['display'] if issue.get('qaEngineer', None) else None
    issue['queue'] = ast.literal_eval(issue['queue'])['display'] if issue.get('queue', None) else None
    issue['resolution'] = ast.literal_eval(issue['resolution'])['display'] if issue.get('resolution', None) else None
    issue['resolvedBy'] = ast.literal_eval(issue['resolvedBy'])['display'] if issue.get('resolvedBy', None) else None
    issue['status'] = ast.literal_eval(issue['status'])['display'] if issue.get('status', None) else None
    issue['statusType'] = ast.literal_eval(issue['statusType'])['display'] if issue.get('statusType', None) else None
    issue['typeOf'] = ast.literal_eval(issue['typeOf'])['display'] if issue.get('typeOf', None) else None
    issue['updatedBy'] = ast.literal_eval(issue['updatedBy'])['display'] if issue.get('updatedBy', None) else None
    issue['stand'] = ', '.join(ast.literal_eval(issue['stand'])) if issue.get('stand', None) else None
    issue['developer'] = ast.literal_eval(issue['developer'])['display'] if issue.get('developer', None) else None

    issue['emailTo'] = ', '.join(ast.literal_eval(issue['emailTo'])) if issue.get('emailTo', None) else None
    issue['regress'] = ', '.join(ast.literal_eval(issue['regress'])) if issue.get('regress', None) else None
    issue['Frontend'] = ', '.join([frontend['display'] for frontend in ast.literal_eval(issue['Frontend'])]) if issue.get('Frontend', None) else None

    # issue['emailTo'] = ', '.join(ast.literal_eval(issue['emailTo'])) if issue.get('emailTo', None) else None
    issue['local_eeEngineer'] = ast.literal_eval(issue['local_eeEngineer'])['display'] if issue.get('local_eeEngineer', None) else None
    issue['eeEngineer'] = ast.literal_eval(issue['eeEngineer'])['display'] if issue.get('eeEngineer', None) else None
    issue['Team'] = ', '.join([frontend['display'] for frontend in ast.literal_eval(issue['Team'])]) if issue.get('Team', None) else None
    issue['aliases'] =  ', '.join(ast.literal_eval(issue['aliases'])) if issue.get('aliases', None) else None
    issue['lastQueue'] = ast.literal_eval(issue['lastQueue'])['display'] if issue.get('lastQueue', None) else None
    issue['previousQueue'] = ast.literal_eval(issue['previousQueue'])['display'] if issue.get('previousQueue', None) else None
    issue['Size'] = ', '.join(ast.literal_eval(issue['Size'])) if issue.get('Size', None) else None

async def get_duration(changes):
    start_date = None
    end_date = None
    for change in changes:
        for field_change in change['fields']:
            if field_change['field'].id != 'status':
                continue

            to_status = field_change['to'].key if field_change['to'] else ''
            if not start_date and to_status == 'inProgress':  # "В РАБОТЕ"
                start_date = safe_parse_iso(change['updatedAt'])
            elif not end_date and to_status == 'closedDev':  # "Готово - Есть на Dev"
                end_date = safe_parse_iso(change['updatedAt'])
                break

    duration = int((end_date - start_date).days) if start_date and end_date else ""

def run_migrations():
    # logger.info("Запускаем миграции")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(base_dir, '..', 'alembic.ini')

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, 'database', 'alembic'))

    command.upgrade(alembic_cfg, 'head')

    # logger.info("Миграции завершены")

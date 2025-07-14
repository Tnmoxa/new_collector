import ast
import os
from datetime import datetime, timedelta, timezone

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
    new_removed = []
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


async def get_status_duration(issue, issue_ref, queue):
    statuses = {'BLOCKS': {'backlog': 'Беклог', 'closedDev': 'Готово - Есть на Dev', 'dorabotka': 'Доработка',
                           'inProgress': 'В работе', 'inReview': 'Ревью', 'novaja': 'Новая',
                           'oceredNaQa': 'Очередь на QA', 'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom',
                           'testing': 'Тестируется', 'zablokirovana': 'Заблокирована'},
                'BUG': {'backlog': 'Беклог', 'bagpodtverzhden': 'Баг подтвержден', 'closed': 'Закрыт',
                        'closedDev': 'Готово - Есть на Dev', 'inProgress': 'В работе',
                        'needsProcessing': 'Нужна обработка', 'otklonen': 'Отклонен', 'testing': 'Тестируется'},
                'ENGEEJL': {'backlog': 'Беклог', 'closedDev': 'Готово - Есть на Dev',
                            'closedProd': 'Закрыто - Есть на проде', 'inProgress': 'В работе', 'inReview': 'Ревью',
                            'novaja': 'Новая', 'oceredNaQa': 'Очередь на QA',
                            'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom', 'testing': 'Тестируется',
                            'zablokirovana': 'Заблокирована'},
                'ENGEETES': {'beklog': 'Бэклог', 'inProgress': 'В работе', 'inReview': 'Ревью', 'novaja': 'Новая',
                             'tehniceskijProekt': 'Технический проект', 'zablokirovana': 'Заблокирована',
                             'zakryta': 'Закрыта'},
                'NWO': {'acceptance': 'Приемка', 'backlog': 'Беклог', 'bagpodtverzhden': 'Баг подтвержден',
                        'dizajn': 'Дизайн', 'estNaDev': 'Есть на DEV', 'gotovokrazrabotke': 'Готово к разработке',
                        'inProgress': 'В работе', 'needsProcessing': 'Нужна обработка', 'needsTZ': 'Нужно ТЗ',
                        'new': 'Новый', 'novaja': 'Новая', 'otklonen': 'Отклонен', 'otmenena': 'Отменена',
                        'testing': 'Тестируется', 'testplan': 'Тест план', 'tpRndPoc': 'ТП. RnD, PoC',
                        'tpVRabote': 'ТП. В работе', 'transferredtothedevelopers': 'Передано разработчикам',
                        'vrazrabotke': 'В разработке', 'zakryta': 'Закрыта'},
                'NWOB': {'backlog': 'Беклог', 'closedDev': 'Готово - Есть на Dev', 'inProgress': 'В работе',
                         'inReview': 'Ревью', 'novaja': 'Новая', 'obrabotka': 'Обработка',
                         'oceredNaQa': 'Очередь на QA', 'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom',
                         'proverkaPostanovsikom': 'Проверка постановщиком', 'testing': 'Тестируется',
                         'zablokirovana': 'Заблокирована', 'zakryta': 'Закрыта'},
                'NWOBUG': {'bagpodtverzhden': 'Баг подтвержден', 'checkforProduction': 'Проверить на Production',
                           'dubl': 'Дубль', 'inProgress': 'В работе', 'new': 'Новый', 'onHold': 'Приостановлено',
                           'testing': 'Тестируется', 'thebugislocalized': 'Баг локализован',
                           'transferredtothedevelopers': 'Передано разработчикам', 'zakryta': 'Закрыта',
                           'zhdetreliz': 'Ждет релиз'},
                'NWOCG': {'backlog': 'Беклог', 'cancelled': 'Отменено', 'closedDev': 'Готово - Есть на Dev',
                          'inProgress': 'В работе', 'inReview': 'Ревью', 'novaja': 'Новая',
                          'oceredNaQa': 'Очередь на QA', 'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom',
                          'testing': 'Тестируется', 'zablokirovana': 'Заблокирована'},
                'NWOF': {'backlog': 'Беклог', 'closedDev': 'Готово - Есть на Dev', 'dizajnrevju': 'Дизайн-ревью',
                         'inProgress': 'В работе', 'novaja': 'Новая', 'oceredNaQa': 'Очередь на QA',
                         'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom', 'testing': 'Тестируется',
                         'zablokirovana': 'Заблокирована'},
                'NWOM': {'backlog': 'Беклог', 'closed': 'Закрыт', 'closedDev': 'Готово - Есть на Dev',
                         'inProgress': 'В работе', 'inReview': 'Ревью', 'novaja': 'Новая',
                         'oceredNaQa': 'Очередь на QA', 'protestirovanoNaDevCustom': 'Протестировано на Dev-Custom',
                         'testing': 'Тестируется', 'zablokirovana': 'Заблокирована', 'zakryta': 'Закрыта'},
                'PROBLOCKS': {'gotovokrazrabotke': 'Готово к разработке', 'new': 'Новый', 'otmenena': 'Отменена',
                              'vrazrabotke': 'В разработке', 'zhdetreliz': 'Ждет релиз'},
                'XBLOCKS': {'beklog': 'Бэклог', 'closed': 'Закрыт', 'inProgress': 'В работе', 'new': 'Новый',
                            'novaja': 'Новая', 'open': 'Открыт'}}

    statuses = {
        'queue1': {'zakryta', 'cancelled', 'obrabotka', 'protestirovanoNaDevCustom', 'testing', 'zablokirovana', 'dizajnrevju', 'closedDev', 'inReview', 'closed', 'novaja', 'inProgress', 'proverkaPostanovsikom', 'beklog', 'tehniceskijProekt', 'oceredNaQa', 'backlog', 'closedProd'},
        'queue2': {'onHold', 'transferredtothedevelopers', 'zakryta', 'thebugislocalized', 'zhdetreliz', 'testing', 'closedDev', 'closed', 'inProgress', 'checkforProduction', 'needsProcessing', 'dubl', 'otklonen', 'bagpodtverzhden', 'backlog', 'new'},
        'queue3': {'zakryta', 'otmenena', 'novaja', 'bagpodtverzhden', 'transferredtothedevelopers', 'gotovokrazrabotke', 'acceptance', 'inProgress', 'vrazrabotke', 'backlog', 'dizajn', 'tpRndPoc', 'estNaDev', 'otklonen', 'new', 'testing', 'testplan', 'tpVRabote', 'needsProcessing', 'needsTZ'},
        'queue4': {'zhdetreliz', 'inReview', 'protestirovanoNaDevCustom', 'gotovokrazrabotke', 'closedDev', 'testing', 'zablokirovana', 'otmenena', 'novaja', 'inProgress', 'beklog', 'closed', 'open', 'dorabotka', 'vrazrabotke', 'oceredNaQa', 'backlog', 'new'}
        }

    d = {}
    for i in statuses[queue]:
        d[i] = {'start_time': (datetime.now(timezone.utc) + timedelta(hours=3)), 'duration': timedelta(seconds=0)}

    changes = issue_ref.changelog.get_all()._data
    to_status = None
    for change in changes:
        for field_change in change['fields']:
            if field_change['field'].id != 'status':
                continue

            to_status = field_change['to'].key if field_change['to'] else ''
            from_status = field_change['from'].key if field_change['from'] else ''

            d[to_status]['start_time'] = safe_parse_iso(change['updatedAt'])
            if from_status:
                d[from_status]['duration'] = d[from_status]['duration'] + safe_parse_iso(change['updatedAt']) - \
                                             d[from_status]['start_time']

    if to_status:
        d[to_status]['duration'] = d[to_status]['duration'] + (datetime.now(timezone.utc) + timedelta(hours=3)) - \
                                   d[to_status]['start_time']

    for i in statuses[queue]:
        issue['dur_' + i] = str(round(d[i]['duration'].total_seconds() / 3600, 2))


async def parse_dicts_from_queues(issue, issue_ref, queue):
    await get_status_duration(issue, issue_ref, queue)
    issue['assignee'] = ast.literal_eval(issue['assignee'])['display'] if issue.get('assignee', None) else None
    issue['boards'] = ', '.join([board['name'] for board in ast.literal_eval(issue['boards'])]) if issue.get('boards',
                                                                                                             None) else None
    issue['components'] = ', '.join(
        [component['display'] for component in ast.literal_eval(issue['components'])]) if issue.get('components',
                                                                                                    None) else None
    issue['createdBy'] = ast.literal_eval(issue['createdBy'])['display'] if issue.get('createdBy', None) else None
    issue['followers'] = ', '.join(
        [follower['display'] for follower in ast.literal_eval(issue['followers'])]) if issue.get('followers',
                                                                                                 None) else None
    issue['link'] = ('https://tracker.yandex.ru/' + issue['link'].split('/')[-1]) if issue.get('link', None) else None
    issue['parent'] = ast.literal_eval(issue['parent'])['key'] if issue.get('parent', None) else None
    issue['pendingReplyFrom'] = ', '.join(
        [reply['display'] for reply in ast.literal_eval(issue['pendingReplyFrom'])]) if issue.get('pendingReplyFrom',
                                                                                                  None) else None
    issue['tags'] = ', '.join(ast.literal_eval(issue['tags'])) if issue.get('tags', None) else None
    issue['previousStatus'] = ast.literal_eval(issue['previousStatus'])['display'] if issue.get('previousStatus',
                                                                                                None) else None
    issue['previousStatusLastAssignee'] = ast.literal_eval(issue['previousStatusLastAssignee'])['display'] if issue.get(
        'previousStatusLastAssignee', None) else None

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
    issue['Frontend'] = ', '.join(
        [frontend['display'] for frontend in ast.literal_eval(issue['Frontend'])]) if issue.get('Frontend',
                                                                                                None) else None

    # issue['emailTo'] = ', '.join(ast.literal_eval(issue['emailTo'])) if issue.get('emailTo', None) else None
    issue['local_eeEngineer'] = ast.literal_eval(issue['local_eeEngineer'])['display'] if issue.get('local_eeEngineer',
                                                                                                    None) else None
    issue['eeEngineer'] = ast.literal_eval(issue['eeEngineer'])['display'] if issue.get('eeEngineer', None) else None
    issue['Team'] = ', '.join([frontend['display'] for frontend in ast.literal_eval(issue['Team'])]) if issue.get(
        'Team', None) else None
    issue['aliases'] = ', '.join(ast.literal_eval(issue['aliases'])) if issue.get('aliases', None) else None
    issue['lastQueue'] = ast.literal_eval(issue['lastQueue'])['display'] if issue.get('lastQueue', None) else None
    issue['previousQueue'] = ast.literal_eval(issue['previousQueue'])['display'] if issue.get('previousQueue',
                                                                                              None) else None
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

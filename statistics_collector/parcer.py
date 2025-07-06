import asyncio
import csv
from datetime import datetime

from database.models import ReturnToWorkFromTests, ReturnToWorkFromReview, DevDuration, Issues
from dependencies import client
from utils import save_stat_record, clear_table, safe_parse_iso

async def parse_stat():
    await generate_report_test_to_work()
    await generate_report_to_design_review_and_back()
    await generate_dev_duration_report()
    await parse_all_data()



async def parse_all_data():
    queues = ['NWOF', 'NWOB', 'ENGEEJL', 'NWOM', 'NWOCG', 'ENGEETESTS', 'BUG', 'NWOBUGS', 'NWO', 'PROBLOCKS',
    'BLOCKS','XBLOCKS']
    print(f"Запущена функция: {parse_all_data.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    from_date = "2025-01-01"
    to_date = datetime.now().strftime("%Y-%m-%d")
    a = []
    await clear_table(Issues)
    for queue in queues:
        print('Обрабатываю', queue)
        issues = client.issues.find(
            filter={
                'queue': queue,
                'created': {'from': from_date, 'to': to_date}
            },
        )

        for issue in issues:
            issue_as_dict = {k: str(v) for k, v in issue.as_dict().items()}
            issue_as_dict['link']=issue_as_dict['self']
            issue_as_dict['typeOf']=issue_as_dict['type']
            del issue_as_dict['self']
            del issue_as_dict['type']
            await save_stat_record(issue_as_dict, Issues, a)
        print(a)



async def generate_report_test_to_work():
    queues = ["NWOCG", "NWOF", "NWOB", "NWOM", "ENGEEJL"]
    print(f"Запущена функция: {generate_report_test_to_work.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    from_date = "2025-01-01"
    to_date = datetime.now().strftime("%Y-%m-%d")

    await clear_table(ReturnToWorkFromTests)

    for queue in queues:
        print('Обрабатываю', queue)
        issues = client.issues.find(
            filter={
                'queue': queue,
                'created': {'from': from_date, 'to': to_date}
            },
        )

        for issue in issues:
            changes = issue.changelog.get_all()._data
            counter = 0

            for change in changes:
                for field_change in change['fields']:
                    if (
                            field_change['field'].id == 'status'
                            and (field_change.get('from').key if field_change.get('from') else None) == 'testing'
                            and (field_change.get('to').key if field_change.get('to') else None) == 'inProgress'
                    ):
                        counter += 1

            await save_stat_record({
                'queue': queue,
                'priority': issue.priority.name if issue.priority else "",
                'type': issue.type.name if issue.type else "",
                'key': issue.key,
                'summary': issue.summary,
                'assignee': issue.assignee.display if issue.assignee else "Не назначен",
                'status': issue.status.display,
                'returns_to_work': counter
            }, ReturnToWorkFromTests)

    print(f"Завершена функция: {generate_report_test_to_work.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def generate_report_to_design_review_and_back(csv_locale = 'sheets'):
    queues = ['ENGEEJL', 'NWOF', 'NWOB', 'NWOCG', 'NWOM']

    print(f"Запущена функция: {generate_report_to_design_review_and_back.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from_date = "2025-01-01"
    to_date = datetime.now().strftime("%Y-%m-%d")

    await clear_table(ReturnToWorkFromReview)

    sep = ',' if csv_locale == 'excel' else ';'
    for queue in queues:
        print('Обрабатываю', queue)
        issues = client.issues.find(
            filter={
                'queue': queue,
                'created': {'from': from_date, 'to': to_date}
            },
        )

        for issue in issues:
            changes = issue.changelog.get_all()._data
            counter = 0


            prev_status = None
            for i, change in enumerate(changes):
                for field_change in change['fields']:
                    if not prev_status:
                        if (field_change['field'].id == 'status'
                                and field_change['to'].key == 'dizajnrevju' if field_change['to'] else False):  # "Дизайн-ревью"
                            prev_status = field_change['from'].key
                    else:
                        if (field_change['field'].id == 'status'):
                            if (((field_change['from'].key == 'dizajnrevju' if field_change['from'] else False)  # "Дизайн-ревью"
                                    and (field_change['to'].key == prev_status if field_change['to'] else False))
                                or
                                ((field_change['from'].key == 'dizajnrevju' if field_change['from'] else False)  # "Дизайн-ревью"
                                    and (field_change['to'].key == 'oceredNaQa' if field_change['to'] else False)
                                    and (prev_status == 'testing'))
                                ):
                                counter += 1
                                prev_status = None

            await save_stat_record({
                'queue': queue,
                'priority': issue.priority.name if issue.priority else "",
                'type': issue.type.name if issue.type else "",
                'key': f'=HYPERLINK("https://tracker.yandex.ru/{issue.key}"{sep} "{issue.key}")',
                'summary': issue.summary,
                'assignee': issue.assignee.display if issue.assignee else "Не назначен",
                'status': issue.status.display,
                'returns_to_work_from_design_review': counter
            }, ReturnToWorkFromReview)

    print(f"Завершена функция: {generate_report_to_design_review_and_back.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def generate_dev_duration_report(csv_locale=0):
    header = [
        'Очередь', 'Приоритет', 'Тип', 'Ключ', 'Задача', 'Исполнитель', 'Текущий статус',
        'Дата начала разработки', 'Дата готовности на Dev', 'Длительность (дней)', 'Теги родительской задачи'
    ]
    queues = ['ENGEEJL', 'NWOF', 'NWOB', 'NWOCG', 'NWOM']

    print(f"Запущена функция: {generate_dev_duration_report.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from_date = "2025-01-01"
    to_date = datetime.now().strftime("%Y-%m-%d")

    await clear_table(DevDuration)

    sep = ',' if csv_locale == 'excel' else ';'

    for queue in queues:
        print('Обрабатываю', queue)
        issues = client.issues.find(
            filter={
                'queue': queue,
                'created': {'from': from_date, 'to': to_date}
            },
        )

        for issue in issues:
            changes = issue.changelog.get_all()._data
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

            parent_tag = issue.parent.key if issue.parent else ''

            await save_stat_record({
                'queue': queue,
                'priority': issue.priority.name if issue.priority else "",
                'type': issue.type.name if issue.type else "",
                'key': f'=HYPERLINK("https://tracker.yandex.ru/{issue.key}"{sep} "{issue.key}")',
                'summary': issue.summary,
                'assignee': issue.assignee.display if issue.assignee else "Не назначен",
                'status': issue.status.display,
                'start_date': start_date.strftime('%Y-%m-%d %H:%M') if start_date else "—",
                'end_date': end_date.strftime('%Y-%m-%d %H:%M') if end_date else "—",
                'duration': str(duration),
                'parent_tag': parent_tag or "—"
            }, DevDuration)


    print(f"Завершена функция: {generate_dev_duration_report.__name__}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    asyncio.run(parse_stat())

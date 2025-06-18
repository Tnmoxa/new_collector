import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from parcer import parse_stat
from utils import run_migrations


async def main():
    run_migrations()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        parse_stat,
        IntervalTrigger(days=1)
    )
    scheduler.start()
    await parse_stat()

    stop_event = asyncio.Event()

    try:
        await stop_event.wait()  # блокируем "вечно", пока не произойдёт завершение
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    run_migrations()
    asyncio.run(main())

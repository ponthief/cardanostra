import asyncio
from typing import List
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import catch_everything_and_restart

db = Database("ext_cardanostra")

cardanostra_ext: APIRouter = APIRouter(prefix="/cardanostra", tags=["cardanostra"])

scheduled_tasks: List[asyncio.Task] = []

cardanostra_static_files = [
    {
        "path": "/cardanostra/static",
        "app": StaticFiles(packages=[("lnbits", "extensions/cardanostra/static")]),
        "name": "cardanostra_static",
    }
]


def cardanostra_renderer():
    return template_renderer(["lnbits/extensions/cardanostra/templates"])


from .tasks import start_bot, restart_bot, every
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


def cardanostra_start():    
    loop = asyncio.get_event_loop()
    task1 = loop.create_task(catch_everything_and_restart(start_bot))    
    # restart Nostr relay connection once every 8 hours as it's getting disconnected         
    task2 = loop.create_task(every(8 * 3600, restart_bot))              
    scheduled_tasks.extend([task1, task2])

def cardanostra_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)    
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
    task1.set_name("CardaNostra") 
    # restart Nostr relay connection once a day as it's getting diconnected
    task2 = loop.create_task(every(24 * 3600, restart_bot))          
    scheduled_tasks.append(task1)
    scheduled_tasks.append(task2)
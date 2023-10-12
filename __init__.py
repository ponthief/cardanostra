import asyncio
from typing import List
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import catch_everything_and_restart


db = Database("ext_nostrboltcardbot")

nostrboltcardbot_ext: APIRouter = APIRouter(prefix="/nostrboltcardbot", tags=["nostrboltcardbot"])

scheduled_tasks: List[asyncio.Task] = []

nostrboltcardbot_static_files = [
    {
        "path": "/nostrboltcardbot/static",
        "app": StaticFiles(packages=[("lnbits", "extensions/nostrboltcardbot/static")]),
        "name": "nostrboltcardbot_static",
    }
]


def nostrboltcardbot_renderer():
    return template_renderer(["lnbits/extensions/nostrboltcardbot/templates"])


from .tasks import start_bot, check_reconnect
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


def nostrboltcardbot_start():
    loop = asyncio.get_event_loop()
    task1 = loop.create_task(catch_everything_and_restart(start_bot))
    scheduled_tasks.append(task1)
    # task2 = loop.create_task(catch_everything_and_restart(check_reconnect))
    # scheduled_tasks.append(task2)
import asyncio
from typing import List
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from .views import cardanostra_generic_router
from .views_api import cardanostra_api_router
from .tasks import start_bot, every, restart_bot

cardanostra_ext: APIRouter = APIRouter(prefix="/cardanostra", tags=["cardanostra"])
cardanostra_ext.include_router(cardanostra_generic_router)
cardanostra_ext.include_router(cardanostra_api_router)
scheduled_tasks: List[asyncio.Task] = []

cardanostra_static_files = [
    {
        "path": "/cardanostra/static",
        "app": StaticFiles(packages=[("lnbits", "extensions/cardanostra/static")]),
        "name": "cardanostra_static",
    }
]

def cardanostra_start():
    from lnbits.tasks import create_permanent_unique_task    
    task1 = create_permanent_unique_task("ext_cardanostra", start_bot)    
    loop = asyncio.get_event_loop()    
    # restart Nostr relay connection once every 8 hours as it's getting disconnected  
    task2 = loop.create_task(every(8 * 3600, restart_bot))    
    scheduled_tasks.extend([task1, task2])

def cardanostra_stop():    
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)
__all__ = [    
    "cardanostra_ext",
    "cardanostra_static_files",
    "cardanostra_start",
    "cardanostra_stop",
] 
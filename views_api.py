# views_api.py is for you API endpoints that could be hit by another service

# add your dependencies here

from lnbits.decorators import WalletTypeInfo, require_admin_key

from . import nostrboltcardbot_ext
from http import HTTPStatus
from fastapi import APIRouter, Depends, Query
from starlette.exceptions import HTTPException
from lnbits.decorators import WalletTypeInfo, require_admin_key
from lnbits.settings import settings

from .crud import (
    create_nostrboltbot_settings,
    delete_nostrboltbot_settings,
    get_nostrboltbot_settings,
    update_nostrboltbot_settings,
    set_nostrbot_card_data,
    delete_nostrbot_card,    
    get_nostrbotcard_by_uid,    
    update_nostrbotcard,
)
from .models import (
    BotInfo,
    BotSettings,
    CreateBotSettings,    
    UpdateBotSettings,
    NostrCardData
)

try:
    from .tasks import get_client, start_bot, stop_bot

    can_run_bot = True
except ImportError as e:

    def get_client(token: str):
        return None

    async def start_bot(bot_settings: BotSettings):
        return None

    async def stop_bot(bot_settings: BotSettings):
        return None

    raise

    can_run_bot = False

nostrboltcardbot_api: APIRouter = APIRouter(prefix="/api/v1", tags=["nostrbotcard"])
# add your endpoints here

async def require_bot_settings(
    wallet_info: WalletTypeInfo = Depends(require_admin_key),
):
    settings = await get_nostrboltbot_settings(wallet_info.wallet.user)
    if not settings:
        raise HTTPException(status_code=400, detail="No bot created")
    if not settings.standalone and not can_run_bot:
        raise HTTPException(
            status_code=400, detail="Can not run Nostr BoltCard Bot bots on this instance"
        )
    return settings


@nostrboltcardbot_api.delete("/settings", status_code=HTTPStatus.OK)
async def api_extension_delete(usr: str = Query(...)):
    settings = await get_nostrboltbot_settings(usr)
    if settings:
        await stop_bot()
        await delete_nostrboltbot_settings(settings.admin)


# Card Control

@nostrboltcardbot_ext.post("/create", status_code=HTTPStatus.CREATED)
async def set_card(data: NostrCardData):    
    return set_nostrbot_card_data(data)

@nostrboltcardbot_ext.post("/update", status_code=HTTPStatus.OK)
async def update_card(data: NostrCardData):    
    return update_nostrbotcard(data)

@nostrboltcardbot_ext.delete("/{car_uid}", status_code=HTTPStatus.OK)
async def delete_nostrbot_card(card_uid: str):    
    return delete_nostrbot_card(card_uid) 
# Bot Control

@nostrboltcardbot_api.get(
    "/bot",
    description="Get the current status of your registered bot",
    status_code=HTTPStatus.OK,
    response_model=BotInfo,
)
async def api_bot_status(bot_settings: BotSettings = Depends(require_bot_settings)):
    client = get_client('nostrboltcardbot')
    return BotInfo.from_client(bot_settings, client)


@nostrboltcardbot_api.post(
    "/bot",
    description="Create and start a new bot (only one per user)",
    status_code=HTTPStatus.OK,
    response_model=BotInfo,
)
async def api_create_bot(
    data: CreateBotSettings, wallet_type: WalletTypeInfo = Depends(require_admin_key)
):
    bot_settings = await create_nostrboltbot_settings(data, wallet_type.wallet.user)
    if not bot_settings.standalone:
        if wallet_type.wallet.id == settings.super_user:
            client = await start_bot(bot_settings)
        else:
            raise HTTPException(
                status_code=400,
                detail="Only the super user can host directly on the instance",
            )
    else:
        client = None
    return BotInfo.from_client(bot_settings, client)


@nostrboltcardbot_api.delete(
    "/bot",
    status_code=HTTPStatus.OK,
)
async def api_delete_bot(bot_settings: BotSettings = Depends(require_bot_settings)):
    if not bot_settings.standalone:
        await stop_bot()
    await delete_nostrboltbot_settings(bot_settings.admin)


@nostrboltcardbot_api.patch(
    "/bot",
    status_code=HTTPStatus.OK,
)
async def api_update_bot(
    data: UpdateBotSettings, bot_settings: BotSettings = Depends(require_bot_settings)
):
    bot_settings = await update_nostrboltbot_settings(data, bot_settings.admin)
    if not bot_settings.standalone:
        await start_bot(bot_settings)


@nostrboltcardbot_api.get("/bot/start", status_code=HTTPStatus.OK, response_model=BotInfo)
async def api_bot_start(bot_settings: BotSettings = Depends(require_bot_settings)):
    if bot_settings.standalone:
        raise HTTPException(status_code=400, detail="Standalone bot cannot be started")
    client = await start_bot(bot_settings)
    return BotInfo.from_client(bot_settings, client)


@nostrboltcardbot_api.get("/bot/stop", status_code=HTTPStatus.OK, response_model=BotInfo)
async def api_bot_stop(bot_settings: BotSettings = Depends(require_bot_settings)):
    if bot_settings.standalone:
        raise HTTPException(status_code=400, detail="Standalone bot cannot be stopped")
    client = await stop_bot()
    return BotInfo.from_client(bot_settings, client)


nostrboltcardbot_ext.include_router(nostrboltcardbot_api)

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import nostrboltcardbot_ext, nostrboltcardbot_renderer

templates = Jinja2Templates(directory="templates")


@nostrboltcardbot_ext.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(check_user_exists),
):
    return nostrboltcardbot_renderer().TemplateResponse(
        "nostrboltcardbot/index.html", {"request": request, "user": user.dict()}
    )

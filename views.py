from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import cardanostra_ext, cardanostra_renderer

templates = Jinja2Templates(directory="templates")


@cardanostra_ext.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(check_user_exists),
):
    return cardanostra_renderer().TemplateResponse(
        "cardanostra/index.html", {"request": request, "user": user.dict()}
    )

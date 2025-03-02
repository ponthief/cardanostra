from fastapi import APIRouter, Depends, Request
from starlette.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

cardanostra_generic_router = APIRouter()

def cardanostra_renderer():
    return template_renderer(["cardanostra/templates"])

@cardanostra_generic_router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(check_user_exists),
):
    return cardanostra_renderer().TemplateResponse(
        "cardanostra/index.html", {"request": request, "user": user.json()}
    )

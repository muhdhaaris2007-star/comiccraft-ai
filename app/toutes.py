from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from app.config import settings
from app.models import PromptRequest
from app.services.comic_service import (
    generate_comic,
)
from app.services.image_generator import (
    generate_image,
)


router = APIRouter()

templates = Jinja2Templates(
    directory=str(
        settings.templates_dir
    )
)


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):

    try:

        payload = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        title, layout, pdf_url = (
            generate_comic(payload)
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "app_name": settings.app_name,
                "title": title,
                "layout": layout,
                "pdf_url": pdf_url,
            },
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_name": settings.app_name,
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
)
async def generate_json(
    payload: PromptRequest,
):

    try:

        title, layout, pdf_url = (
            generate_comic(payload)
        )

        return JSONResponse(
            {
                "title": title,
                "layout": [
                    panel.model_dump()
                    for panel in layout
                ],
                "pdf_url": pdf_url,
            }
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get(
    "/test-image",
)
async def test_image(
    prompt: str = (
        "a brave fox in an enchanted forest"
    ),
):

    try:

        path = generate_image(
            prompt,
            0,
        )

        return {
            "image_url": (
                f"/static/{path}"
            ),
            "path": path,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
    pdf_url: str = "",
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "app_name": settings.app_name,
            "pdf_url": pdf_url,
        },
    )


@router.get(
    "/download/{filename}",
)
async def download_pdf(
    filename: str,
):

    safe_name = Path(filename).name

    pdf_path = (
        settings.exports_dir /
        safe_name
    )

    if (
        not pdf_path.exists()
        or pdf_path.suffix.lower() != ".pdf"
    ):

        raise HTTPException(
            status_code=404,
            detail="PDF not found.",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
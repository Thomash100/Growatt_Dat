from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.models import ControlSettings
from app.web.i18n import SUPPORTED_LANGUAGES, browser_translations, normalize_language, translate


router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _service(request: Request):
    return request.app.state.service


def _template_context(request: Request, **extra):
    service = _service(request)
    language = normalize_language(service.settings.ui_language)
    context = {
        "settings": service.settings.to_dict(),
        "language": language,
        "languages": SUPPORTED_LANGUAGES,
        "i18n": browser_translations(language),
        "t": lambda key: translate(key, language),
    }
    context.update(extra)
    return context


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _template_context(request, state=_service(request).snapshot()),
    )


@router.get("/live", response_class=HTMLResponse)
async def live(request: Request):
    return templates.TemplateResponse(
        request,
        "live.html",
        _template_context(request, state=_service(request).snapshot()),
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(
        request,
        "settings.html",
        _template_context(request, error=None),
    )


@router.post("/settings", response_class=HTMLResponse)
async def update_settings_form(request: Request):
    service = _service(request)
    form = dict(await request.form())
    if "zero_export_enabled" not in form:
        form["zero_export_enabled"] = "false"
    try:
        settings = ControlSettings.from_mapping(form, base=service.settings)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "settings.html",
            _template_context(request, error=str(exc)),
            status_code=400,
        )
    await service.update_settings(settings)
    return RedirectResponse("/settings", status_code=303)


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    logs = _service(request).store.get_logs(limit=200)
    return templates.TemplateResponse(request, "logs.html", _template_context(request, logs=logs))


@router.get("/api/status")
async def api_status(request: Request):
    return _service(request).snapshot()


@router.get("/api/settings")
async def api_settings(request: Request):
    return _service(request).settings.to_dict()


@router.post("/api/settings")
async def api_update_settings(request: Request):
    service = _service(request)
    payload = await request.json()
    try:
        settings = ControlSettings.from_mapping(payload, base=service.settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await service.update_settings(settings)
    return settings.to_dict()


@router.get("/api/measurements/latest")
async def api_latest_measurement(request: Request):
    measurement = _service(request).latest_measurement or _service(request).store.get_latest_measurement()
    if measurement is None:
        raise HTTPException(status_code=404, detail="No measurement available yet")
    return measurement.to_dict()


@router.get("/api/measurements/history")
async def api_measurement_history(request: Request, limit: int = Query(default=200, ge=1, le=2000)):
    return [item.to_dict() for item in _service(request).store.get_measurement_history(limit=limit)]


@router.get("/api/control/latest")
async def api_latest_control(request: Request):
    decision = _service(request).latest_decision or _service(request).store.get_latest_control_decision()
    if decision is None:
        raise HTTPException(status_code=404, detail="No control decision available yet")
    return decision.to_dict()

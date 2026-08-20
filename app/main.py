from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.ai import router as ai_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.collaborations import router as collaborations_router
from app.api.v1.health import router as health_router
from app.api.v1.kb import router as kb_router
from app.api.v1.me import router as me_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.signals import router as signals_router
from app.errors import register_error_handlers
from app.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="PANGAEA API", version="0.1.0")
    # In development the frontend may be opened from a phone on the same LAN
    # (http://<mac-ip>:3000), so private-network origins are allowed alongside
    # the configured list. Production keeps the explicit allowlist only.
    private_lan_origins = (
        r"^https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+"
        r"|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?$"
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin_list,
        allow_origin_regex=private_lan_origins if settings.app_env != "production" else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(auth_router)
    application.include_router(health_router)
    application.include_router(me_router)
    application.include_router(profiles_router)
    application.include_router(ai_router)
    application.include_router(signals_router)
    application.include_router(applications_router)
    application.include_router(collaborations_router)
    application.include_router(chat_router)
    application.include_router(kb_router)
    application.include_router(notifications_router)
    return application


app = create_app()

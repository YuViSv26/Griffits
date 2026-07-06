import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.db import init_db, seed_games_if_empty
from backend.routers import assessment, auth, chat, games, init, payments, profile

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_games_if_empty()
    logger.info("Backend started: DB ready, games seeded")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Griffiths Neuro Consultant API",
        description="REST API для веб-приложения нейроконсультанта по шкале Гриффитс",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(init.router)
    app.include_router(profile.router)
    app.include_router(assessment.router)
    app.include_router(games.router)
    app.include_router(payments.router)
    app.include_router(chat.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, benchmarks, blueprints, events, health, phase1_exit, platform, tasks, traces, validation
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Runtime Layer", version="5.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(traces.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    app.include_router(blueprints.router, prefix="/api")
    app.include_router(platform.router, prefix="/api")
    app.include_router(validation.router, prefix="/api")
    app.include_router(benchmarks.router, prefix="/api")
    app.include_router(phase1_exit.router, prefix="/api")

    return app


app = create_app()

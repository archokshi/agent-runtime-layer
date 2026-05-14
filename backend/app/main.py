from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, benchmarks, blueprints, budget, context_memory, corpus, events, evidence, evidence_campaign, health, optimization, phase1_exit, phase2_handoff, platform, settings, tasks, telemetry, traces, validation
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Runtime Layer", version="5.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:4000", "http://127.0.0.1:4000", "http://localhost:8100"],
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
    app.include_router(corpus.router, prefix="/api")
    app.include_router(evidence.router, prefix="/api")
    app.include_router(evidence_campaign.router, prefix="/api")
    app.include_router(phase2_handoff.router, prefix="/api")
    app.include_router(telemetry.router, prefix="/api")
    app.include_router(optimization.router, prefix="/api")
    app.include_router(budget.router, prefix="/api")
    app.include_router(context_memory.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")

    return app


app = create_app()

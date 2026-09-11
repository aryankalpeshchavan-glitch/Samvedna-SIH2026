import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.core.audit_logger import setup_audit_listeners
from app.core.config import settings
from app.routers import (
    auth_router, health_router, incidents_router, volunteers_router,
    assignments_router, resources_router, risk_router,
    notifications_router, mesh_router, status_router, intelligence_router,
    audit_router, sensors_router,
)
from app.realtime.ws_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_audit_listeners()

    # Load ML prediction service
    from app.services.prediction_service import prediction_service
    prediction_service.load()

    from app.background.auto_reassign import auto_reassign_loop
    from app.background.matching_worker import process_matching_queue
    task = asyncio.create_task(auto_reassign_loop())
    matching_task = asyncio.create_task(process_matching_queue())

    yield

    task.cancel()
    matching_task.cancel()
    try:
        await asyncio.gather(task, matching_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(
    title="CrisisCore",
    description="AI-powered early-warning platform for landslide/flood risk",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://samvedna-sih2026-2cg2r5elz-aj-e6d0.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(volunteers_router)
app.include_router(assignments_router)
app.include_router(resources_router)
app.include_router(risk_router)
app.include_router(notifications_router)
app.include_router(mesh_router)
app.include_router(status_router)
app.include_router(intelligence_router)
app.include_router(audit_router)
app.include_router(sensors_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception safely here if needed, but do not leak to client
    import logging
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, client_id)
    try:
        await ws_manager.subscribe_and_forward(websocket, client_id)
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect(websocket, client_id)

"""FastAPI backend for Maximus.ai React Terminal."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from maximus.api.routes import router as api_router
from maximus.api.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    from maximus.tools.builtin import register_builtin_tools
    from maximus.tools.builtin import register_repo_tools
    
    register_builtin_tools()
    register_repo_tools()
    
    yield
    
    # Shutdown
    pass


app = FastAPI(
    title="Maximus.ai API",
    description="Backend for Maximus.ai React Terminal",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")


@app.get("/")
async def root():
    return {"service": "Maximus.ai API", "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

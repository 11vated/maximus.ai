"""API routes for Maximus.ai."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import asyncio

from maximus.tools.registry import get_registry
from maximus.core.loop import AgentLoop
from maximus.models import AgentConfig


router = APIRouter()


class CommandRequest(BaseModel):
    command: str
    model: Optional[str] = "qwen2.5-coder:7b"
    workdir: Optional[str] = "."


class CommandResponse(BaseModel):
    success: bool
    output: str
    state: Optional[str] = None
    error: Optional[str] = None


class ToolInfo(BaseModel):
    name: str
    description: str
    category: Optional[str] = None
    permission_level: Optional[str] = None


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools():
    """List all registered tools."""
    registry = get_registry()
    tools = []
    for name in registry.list_tools():
        tool = registry.get(name)
        if tool:
            metadata = tool.metadata
            tools.append(ToolInfo(
                name=metadata.name,
                description=metadata.description,
                category=metadata.categories[0] if metadata.categories else None,
                permission_level=metadata.permission_level,
            ))
    return tools


@router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Execute a command via Maximus agent."""
    try:
        config = AgentConfig(model=request.model, workdir=request.workdir)
        agent = AgentLoop(config)
        
        output_chunks = []
        final_state = "unknown"
        
        for event in agent.run(request.command):
            if hasattr(event, 'data'):
                if 'text' in event.type.value:
                    text = event.data.get('text', '')
                    if text:
                        output_chunks.append(text)
                elif 'state' in event.type.value:
                    final_state = event.data.get('state', final_state)
        
        return CommandResponse(
            success=True,
            output=''.join(output_chunks),
            state=final_state,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get system status."""
    import httpx
    
    status = {
        "ollama": False,
        "python": True,
        "tools_count": 0,
    }
    
    # Check Ollama
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
        if resp.is_success:
            status["ollama"] = True
            status["models"] = len(resp.json().get("models", []))
    except Exception:
        pass
    
    # Tool count
    registry = get_registry()
    status["tools_count"] = len(registry.list_tools())
    
    return status


@router.post("/chat")
async def chat(request: CommandRequest):
    """Interactive chat session (streaming response)."""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
        config = AgentConfig(model=request.model, workdir=request.workdir)
        agent = AgentLoop(config)
        
        for event in agent.run(request.command):
            if hasattr(event, 'data'):
                yield json.dumps({
                    "type": event.type.value,
                    "data": event.data,
                }) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")

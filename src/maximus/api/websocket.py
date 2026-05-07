"""WebSocket routes for real-time agent updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
import logging

from maximus.core.loop import AgentLoop
from maximus.models import AgentConfig, Event, EventType

logger = logging.getLogger(__name__)

router = APIRouter()

# Track active connections
active_connections: Dict[str, WebSocket] = {}
# Track sessions
sessions: Dict[str, Dict] = {}


@router.websocket("/agent")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication.

    Message format (client -> server):
    {
        "command": "user input",
        "model": "qwen2.5-coder:7b",
        "workdir": ".",
        "session_id": "optional",
        "context": {}
    }

    Message format (server -> client):
    {
        "type": "thinking|acting|observing|reflecting|done|error",
        "data": {...},
        "session_id": "..."
    }
    """
    await websocket.accept()
    client_id = id(websocket)
    active_connections[client_id] = websocket
    session_id = None

    try:
        while True:
            # Receive command from client
            data = await websocket.receive_text()
            message = json.loads(data)

            command = message.get("command")
            model = message.get("model", "qwen2.5-coder:7b")
            workdir = message.get("workdir", ".")
            session_id = message.get("session_id", f"session_{client_id}")
            context = message.get("context", {})

            # Store session
            if session_id not in sessions:
                sessions[session_id] = {
                    "history": [],
                    "context": context,
                    "created": asyncio.get_event_loop().time(),
                }

            if not command:
                await websocket.send_json({"error": "No command provided", "session_id": session_id})
                continue

            # Execute via agent loop
            try:
                config = AgentConfig(model=model, workdir=workdir)
                agent = AgentLoop(config)

                # Send start event
                await websocket.send_json({
                    "type": "start",
                    "session_id": session_id,
                    "command": command,
                })

                # Run agent loop with event streaming
                for event in agent.run(command):
                    if isinstance(event, Event):
                        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)

                        # Map internal event types to frontend event types
                        frontend_type = event_type
                        message = ""
                        data = event.data if hasattr(event, 'data') and event.data else {}

                        if event_type == "state_change":
                            # Extract state from data
                            state = data.get("state", "unknown") if data else "unknown"
                            frontend_type = state  # thinking, acting, observing, etc.
                            message = data.get("message", f"State: {state}") if data else ""

                        elif event_type == "tool_start":
                            frontend_type = "acting"
                            tool_name = data.get("tool", "unknown") if data else "unknown"
                            message = f"Using tool: {tool_name}"

                        elif event_type == "tool_end":
                            frontend_type = "observing"
                            message = "Tool execution complete"

                        elif event_type == "turn_done":
                            frontend_type = "done"
                            message = "Task completed"

                        # Send event in frontend-expected format
                        await websocket.send_json({
                            "type": frontend_type,
                            "session_id": session_id,
                            "message": message,
                            "data": data
                        })

                        # Store in session history
                        sessions[session_id]["history"].append(event_data)

                # Send completion
                await websocket.send_json({
                    "type": "done",
                    "session_id": session_id,
                })

            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "session_id": session_id,
                })

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.pop(client_id, None)


@router.websocket("/terminal")
async def terminal_websocket(websocket: WebSocket):
    """WebSocket endpoint for terminal-like interaction.

    Message format:
    {
        "action": "command|ping|tool_call",
        "payload": {...}
    }
    """
    await websocket.accept()
    client_id = id(websocket)
    active_connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            payload = message.get("payload", {})

            if action == "command":
                # Execute command via tool system
                command = payload.get("command")
                if command:
                    # Here you'd integrate with actual command execution via tools
                    await websocket.send_json({
                        "type": "output",
                        "content": f"Executed: {command}",
                        "action": "command_result",
                    })

            elif action == "tool_call":
                # Call a specific tool
                tool_name = payload.get("tool")
                tool_args = payload.get("args", {})
                # Integrate with tool registry
                await websocket.send_json({
                    "type": "tool_result",
                    "tool": tool_name,
                    "status": "not_implemented",
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            elif action == "get_tools":
                # Return available tools
                from maximus.tools.registry import registry
                tools = registry.to_schemas()
                await websocket.send_json({
                    "type": "tools_list",
                    "tools": tools,
                })

    except WebSocketDisconnect:
        logger.info(f"Terminal client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
    finally:
        active_connections.pop(client_id, None)


async def broadcast_to_session(session_id: str, message: Dict):
    """Broadcast a message to all connections in a session."""
    disconnected = []
    for client_id, ws in active_connections.items():
        try:
            await ws.send_json({**message, "session_id": session_id})
        except Exception:
            disconnected.append(client_id)

    for client_id in disconnected:
        active_connections.pop(client_id, None)

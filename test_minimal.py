#!/usr/bin/env python
"""Minimal test - bypass complex init."""
import sys
import asyncio
sys.path.insert(0, 'src')

from maximus.utils.llm import LLMClient
from maximus.models import AgentConfig
from maximus.tools.registry import get_registry
from maximus.tools.builtin import register_builtin_tools
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import json

# Register tools
register_builtin_tools()
registry = get_registry()

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]

def extract_tool_calls(text: str) -> List[ToolCall]:
    tool_calls = []
    pattern = r'TOOL_START(\{.*?\})TOOL_END'
    matches = re.findall(pattern, text, re.DOTALL)
    for i, match in enumerate(matches):
        try:
            data = json.loads(match)
            if "name" in data:
                tool_calls.append(ToolCall(
                    id=f"call_{i}",
                    name=data["name"],
                    arguments=data.get("arguments", {})
                ))
        except:
            continue
    return tool_calls

async def main():
    config = AgentConfig()
    config.model = 'qwen2.5-coder:7b'
    client = LLMClient(config)
    
    system = """You are Maximus. Call tools when needed.

Output EXACTLY: TOOL_START{"name": "NAME", "arguments": {"KEY": "VAL"}}TOOL_END

Tools: ls, read_file

Task: list files

Output:"""
    
    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': 'list files'}
    ]
    
    print("Getting LLM response...")
    full = ''
    async for chunk in client.chat(messages):
        if chunk.get('message', {}).get('content'):
            full += chunk['message']['content']
    
    print(f"Response: {full}")
    
    # Extract tool calls
    calls = extract_tool_calls(full)
    print(f"Tool calls: {calls}")
    
    # Execute tool
    if calls:
        tool = calls[0]
        print(f"Executing tool: {tool.name}")
        tool_obj = registry.get(tool.name)
        if tool_obj:
            result = await tool_obj.execute(tool.arguments, {})
            print(f"Result: {result}")
        else:
            print(f"Tool not found: {tool.name}")
    
    print("Done!")

asyncio.run(main())
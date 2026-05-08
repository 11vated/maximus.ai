#!/usr/bin/env python
"""Simple CLI test - mimicking what cli.py does."""
import sys
sys.path.insert(0, 'src')

from maximus.models import AgentConfig
from maximus.chat import ChatSession

print("Creating config...")
config = AgentConfig(model='qwen2.5-coder:7b', workdir='.')

print("Creating session...")
session = ChatSession(workdir='.', config=config)

print("Running agent...")
count = 0
for event in session.agent.run('ls'):
    count += 1
    if event.type.value == "text_chunk":
        txt = event.data.get("text", "")
        if txt:
            print(f"[text] {txt}")
    elif event.type.value == "tool_start":
        print(f"[tool_start] {event.data.get('tool')}")
    elif event.type.value == "tool_end":
        success = event.data.get("success", False)
        result = event.data.get('result', {})
        print(f"[tool_end] {'OK' if success else 'FAIL'} - {result}")
    elif event.type.value == "state_change":
        print(f"[state] {event.data.get('state')}")
    elif event.type.value == "turn_done":
        print(f"[turn_done]")
        
    if count > 20:
        print("Breaking - too many events")
        break

print(f"\nTotal events: {count}")
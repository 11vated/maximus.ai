#!/usr/bin/env python
"""Test full agent tool execution."""
import sys
sys.path.insert(0, 'src')

from maximus.chat.session import ChatSession
from maximus.models import AgentConfig

config = AgentConfig()
config.model = 'qwen2.5-coder:7b'
config.max_model_calls = 2

session = ChatSession(config=config)
print("Running agent...")

events = []
for event in session.agent.run('list files in current directory'):
    events.append(event)
    print(f"Event: {event.type.value} - {event.data}")

print(f"\nTotal events: {len(events)}")
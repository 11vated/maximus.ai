#!/usr/bin/env python
"""Full agent test."""
import sys
sys.path.insert(0, 'src')

print("Creating agent...")
from maximus.models import AgentConfig
from maximus.core.loop import AgentLoop

config = AgentConfig()
config.model = 'qwen2.5-coder:7b'
config.max_model_calls = 3

agent = AgentLoop(config)
gen = agent.run('list files in current directory')

print("Running agent...")
events = []
for event in gen:
    events.append(event)
    print(f"  {event.type.value}: {event.data}")

print(f"\nTotal events: {len(events)}")
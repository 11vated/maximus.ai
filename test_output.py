#!/usr/bin/env python
"""Full agent test with output."""
import sys
sys.path.insert(0, 'src')

print("Creating agent...")
from maximus.models import AgentConfig
from maximus.core.loop import AgentLoop

config = AgentConfig()
config.model = 'qwen2.5-coder:7b'
config.max_model_calls = 2

agent = AgentLoop(config)
gen = agent.run('list files in current directory')

print("Running...")
events = []
for event in gen:
    events.append(event)
    print(f"  {event.type.value}: {event.data}")
    if event.type.value == 'tool_end':
        print(f"    -> Result: {event.data.get('result', {}).get('entries', [])}")

print(f"\nTotal: {len(events)} events")
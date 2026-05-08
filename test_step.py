#!/usr/bin/env python
"""Test agent step by step - without asyncio.run wrapper."""
import sys
sys.path.insert(0, 'src')

print("1. Creating AgentConfig...")
from maximus.models import AgentConfig
config = AgentConfig()
config.model = 'qwen2.5-coder:7b'
config.max_model_calls = 2
print("   Done")

print("2. Creating AgentLoop...")
from maximus.core.loop import AgentLoop
agent = AgentLoop(config)
print("   Done")

print("3. Getting generator...")
gen = agent.run('list files')
print("   Done")

print("4. Getting first event...")
event = next(gen)
print(f"   Got: {event.type.value}")

print("5. Getting second event...")
event = next(gen)
print(f"   Got: {event.type.value}")

print("All done!")
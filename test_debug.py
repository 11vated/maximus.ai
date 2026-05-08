#!/usr/bin/env python
"""Debug agent execution."""
import sys
sys.path.insert(0, 'src')

print("Creating agent...")
from maximus.models import AgentConfig
from maximus.core.loop import AgentLoop

config = AgentConfig()
config.model = 'qwen2.5-coder:7b'
config.max_model_calls = 2

agent = AgentLoop(config)
gen = agent.run('ls')

print("Getting event 1...")
e1 = next(gen)
print(f"  1: {e1.type.value}")

print("Getting event 2...")
e2 = next(gen)
print(f"  2: {e2.type.value}")

print("Getting event 3...")
e3 = next(gen)
print(f"  3: {e3.type.value}")

print("Getting event 4...")
e4 = next(gen)
print(f"  4: {e4.type.value}")

print("Done")
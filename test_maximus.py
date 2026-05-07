"""Test Maximus talk & code."""

import asyncio
from maximus.models import AgentConfig
from maximus.core import AgentLoop

def test_run():
    config = AgentConfig(model='qwen2.5-coder:7b', workdir='.')
    agent = AgentLoop(config)

    print('Maximus talking & coding...\n')

    for event in agent.run('Write a Python hello world script to hello.py'):
        if event.type.value == 'text_chunk':
            text = event.data.get('text', '')
            print(text, end='')
        elif event.type.value == 'tool_start':
            print(f'\n[Tool: {event.data.get("tool")}]')
        elif event.type.value == 'tool_end':
            result = event.data.get('result', {})
            if result.get('success'):
                print(' -> OK')
            else:
                print(f' -> FAIL: {result.get("error")}')
        elif event.type.value == 'state_change':
            print(f'\n[State: {event.data.get("state")}]')

    print('\nDone.')

if __name__ == '__main__':
    test_run()

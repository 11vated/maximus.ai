#!/usr/bin/env python
"""Test tool calling directly."""
import asyncio
import json
import re
import sys
sys.path.insert(0, 'src')

from maximus.utils.llm import LLMClient
from maximus.models import AgentConfig

async def test():
    config = AgentConfig()
    config.model = 'qwen2.5-coder:7b'
    client = LLMClient(config)

    system = """You are Maximus, a coding assistant. Your ONLY job is to call tools.

RULES:
1. Output EXACTLY: TOOL_START{"name": "NAME", "arguments": {"KEY": "VAL"}}TOOL_END
2. No other text when calling tools
3. Use lowercase with underscores

EXAMPLES:
"list files" -> TOOL_START{"name": "ls", "arguments": {"path": "."}}TOOL_END
"read file" -> TOOL_START{"name": "read_file", "arguments": {"path": "file.py"}}TOOL_END

Tools: ls, read_file, write_file, edit_file, execute_shell, grep, glob

Task: list files in current directory

Output now:"""

    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': 'list files'}
    ]

    print('Calling model...')
    full = ''
    async for chunk in client.chat(messages):
        if chunk.get('message', {}).get('content'):
            content = chunk['message']['content']
            full += content

    print('=== Full response ===')
    print(full)
    print('=== End ===')

    # Test extraction
    pattern = r'TOOL_START(\{.*?\})TOOL_END'
    matches = re.findall(pattern, full, re.DOTALL)
    print(f'\nExtracted {len(matches)} tool calls:')
    for m in matches:
        try:
            data = json.loads(m)
            print(f'  - {data}')
        except Exception as e:
            print(f'  - Failed to parse: {m} ({e})')

if __name__ == "__main__":
    asyncio.run(test())
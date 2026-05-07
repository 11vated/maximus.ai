#!/usr/bin/env python
"""Test script to verify Maximus.ai system."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio


async def test_ollama():
    print("=" * 50)
    print("Testing Ollama...")
    print("=" * 50)
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                print(f"[PASS] Ollama running with {len(models)} models:")
                for m in models[:5]:
                    print(f"   - {m['name']}")
                return True
            print(f"[FAIL] Ollama returned status {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Ollama not available: {e}")
        return False


async def test_agent():
    print("\n" + "=" * 50)
    print("Testing Agent Loop...")
    print("=" * 50)
    
    try:
        from maximus.core.loop import AgentLoop
        from maximus.models import AgentConfig
        
        config = AgentConfig(model="qwen2.5-coder:7b", workdir=".")
        agent = AgentLoop(config)
        
        print(f"[PASS] Agent loop created")
        print(f"   State: {agent.state}")
        print(f"   Config model: {agent.config.model}")
        
        schemas = agent._get_tool_schemas()
        print(f"   Tool schemas: {len(schemas)} tools")
        return True
    except Exception as e:
        print(f"[FAIL] Agent loop failed: {e}")
        return False


async def test_tools():
    print("\n" + "=" * 50)
    print("Testing Tool Registration...")
    print("=" * 50)
    
    try:
        from maximus.tools.registry import get_registry
        from maximus.tools.builtin import register_builtin_tools
        
        register_builtin_tools()
        registry = get_registry()
        tools = registry.list_tools()
        
        print(f"[PASS] {len(tools)} tools registered:")
        for tool in tools[:10]:
            print(f"   - {tool}")
        return True
    except Exception as e:
        print(f"[FAIL] Tool registration failed: {e}")
        return False


async def test_memory():
    print("\n" + "=" * 50)
    print("Testing Memory System...")
    print("=" * 50)
    
    try:
        from maximus.memory import MemoryMesh, MemoryBank
        from maximus.intelligence.model_router import get_model_router
        
        mesh = MemoryMesh(".")
        mesh.add("test_key", "test_value", MemoryBank.EPISODIC)
        print("[PASS] MemoryMesh working")
        
        router = get_model_router()
        decision = router.route("write a function to add two numbers")
        print(f"   Model router: {decision.model} ({decision.intent.value})")
        return True
    except Exception as e:
        print(f"[FAIL] Memory system failed: {e}")
        return False


async def test_security():
    print("\n" + "=" * 50)
    print("Testing Security System...")
    print("=" * 50)
    
    try:
        from maximus.security import get_permission_classifier
        
        classifier = get_permission_classifier()
        
        result = classifier.check_command("ls -la")
        print(f"   'ls -la' -> {result.category.value}")
        
        result = classifier.check_command("rm -rf /")
        print(f"   'rm -rf /' -> {result.category.value}")
        
        result = classifier.check_command("git status")
        print(f"   'git status' -> {result.category.value}")
        
        print("[PASS] Security system working")
        return True
    except Exception as e:
        print(f"[FAIL] Security system failed: {e}")
        return False


async def main():
    print("\n" + "=" * 60)
    print("MAXIMUS.AI SYSTEM VERIFICATION")
    print("=" * 60)
    
    results = []
    results.append(("Ollama", await test_ollama()))
    results.append(("Agent Loop", await test_agent()))
    results.append(("Tool Registration", await test_tools()))
    results.append(("Memory System", await test_memory()))
    results.append(("Security System", await test_security()))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"   {name}: [{status}]")
    
    print(f"\nResult: {passed}/{len(results)} tests passed")
    return passed == len(results)


if __name__ == "__main__":
    asyncio.run(main())
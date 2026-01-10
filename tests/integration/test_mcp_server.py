#!/usr/bin/env python3
"""Test script for MCP server to verify it's working correctly."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


async def test_mcp_server():
    """Test the MCP server by sending initialization and list_tools requests."""

    print("🧪 Testing PPTX MCP Server...")
    print("=" * 60)

    # Start the server process with src/ layout on PYTHONPATH
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"
    server_path = src_path / "mcp_server" / "server.py"
    if not server_path.exists():
        print(f"   ❌ Server path not found: {server_path}")
        return False

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(src_path)
    )

    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
        cwd=repo_root,
        env=env,
    )

    try:
        # Test 1: Initialize
        print("\n1️⃣  Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        request_str = json.dumps(init_request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()

        # Read response (with timeout)
        try:
            response_line = await asyncio.wait_for(
                asyncio.to_thread(process.stdout.readline), timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    print("   ✅ Initialization successful!")
                    server_name = (
                        response.get("result", {}).get("serverInfo", {}).get("name", "Unknown")
                    )
                    print(f"   📋 Server info: {server_name}")
                else:
                    print(f"   ❌ Initialization failed: {response}")
                    return False
            else:
                print("   ❌ No response received")
                return False

        except asyncio.TimeoutError:
            print("   ❌ Timeout waiting for response")
            return False

        # Test 2: List tools
        print("\n2️⃣  Testing list_tools...")
        list_tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        request_str = json.dumps(list_tools_request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()

        try:
            response_line = await asyncio.wait_for(
                asyncio.to_thread(process.stdout.readline), timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    tools = response["result"].get("tools", [])
                    print(f"   ✅ Found {len(tools)} tools:")
                    for tool in tools[:5]:  # Show first 5
                        print(f"      • {tool.get('name', 'Unknown')}")
                    if len(tools) > 5:
                        print(f"      ... and {len(tools) - 5} more")
                    return True
                else:
                    print(f"   ❌ List tools failed: {response}")
                    return False
            else:
                print("   ❌ No response received")
                return False

        except asyncio.TimeoutError:
            print("   ❌ Timeout waiting for response")
            return False

    except Exception as e:
        print(f"   ❌ Error during test: {e}")
        return False
    finally:
        # Clean up
        try:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except (PermissionError, ProcessLookupError):
                    pass  # Process may have already terminated
        except (PermissionError, ProcessLookupError):
            pass  # Process may have already terminated or we don't have permission

        # Check for errors in stderr
        try:
            stderr_output = process.stderr.read()
            if stderr_output and "ERROR" in stderr_output:
                print(f"\n⚠️  Server errors:\n{stderr_output}")
        except Exception:
            pass


def test_server_import():
    """Test if server module can be imported."""
    print("\n0️⃣  Testing server module import...")
    try:
        from mcp_server.server import server  # noqa: F401

        print("   ✅ Server module imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Failed to import server: {e}")
        return False


def test_dependencies():
    """Test if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    required = ["mcp", "python_pptx", "lxml"]
    missing = []

    for dep in required:
        try:
            if dep == "python_pptx":
                __import__("pptx")
            elif dep == "mcp":
                __import__("mcp")
            else:
                __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} (missing)")
            missing.append(dep)

    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Run: pip3 install -r requirements.txt")
        return False
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PPTX MCP Server Test Suite")
    print("=" * 60)

    # Test dependencies first
    if not test_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)

    # Test import
    if not test_server_import():
        print("\n❌ Server import failed.")
        sys.exit(1)

    # Test MCP communication
    success = await test_mcp_server()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Server is working correctly.")
        print("\n💡 To use the server:")
        print("   1. Configure it in your MCP client (Cursor, Claude Desktop, etc.)")
        print("   2. The server will be started automatically by the client")
        print("   3. Use natural language to interact with PPTX files")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)


def quick_test():
    """Quick test without process management - just verify imports and structure."""
    print("\n" + "=" * 60)
    print("Quick Server Test")
    print("=" * 60)

    # Test dependencies
    if not test_dependencies():
        return False

    # Test import
    if not test_server_import():
        return False

    # Test that tools are registered
    print("\n3️⃣  Testing tool registration...")
    try:
        from mcp_server.tools.read_tools import get_read_tools
        from mcp_server.tools.edit_tools import get_edit_tools
        from mcp_server.tools.slide_tools import get_slide_tools
        from mcp_server.tools.notes_tools import get_notes_tools

        read_tools = get_read_tools()
        edit_tools = get_edit_tools()
        slide_tools = get_slide_tools()
        notes_tools = get_notes_tools()

        total = len(read_tools) + len(edit_tools) + len(slide_tools) + len(notes_tools)
        print(f"   ✅ Registered {total} tools:")
        print(f"      • {len(read_tools)} read tools")
        print(f"      • {len(edit_tools)} edit tools")
        print(f"      • {len(slide_tools)} slide management tools")
        print(f"      • {len(notes_tools)} notes tools")

        return True
    except Exception as e:
        print(f"   ❌ Tool registration failed: {e}")
        return False


if __name__ == "__main__":
    # Check if --quick flag is provided
    if "--quick" in sys.argv or "-q" in sys.argv:
        success = quick_test()
        if success:
            print("\n✅ Quick test passed! Server structure is correct.")
            print("💡 Run without --quick to test full MCP communication.")
        else:
            print("\n❌ Quick test failed.")
            sys.exit(1)
    else:
        asyncio.run(main())

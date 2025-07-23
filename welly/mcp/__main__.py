#!/usr/bin/env python3
"""
Welly MCP Server CLI

Command-line interface for running the welly MCP server.
This allows the server to be run as a classic MCP server compatible with
Claude Desktop, Cursor, VS Code, and other MCP clients.

Usage:
    python -m welly.mcp
    python welly/mcp/__main__.py
"""

import asyncio
import sys
from .mcp_server import main

if __name__ == "__main__":
    # Run the MCP server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("MCP server stopped.", file=sys.stderr)
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        sys.exit(1)
"""
Welly MCP Server

Model Context Protocol (MCP) server for welly - enables AI assistants to perform
petrophysical analysis using natural language through the welly library.

This module provides:
- MCP server implementation for welly tools
- Well log analysis capabilities 
- Visualization and statistical analysis
- Compatible with Claude, Cursor, and other MCP clients

Usage:
    # As a standalone MCP server
    python -m welly.mcp

    # Programmatic usage
    from welly.mcp import WellyMCPServer
    server = WellyMCPServer()
"""

from .mcp_server import WellyMCPServer
from .tools import WellyMCPTools

__all__ = ['WellyMCPServer', 'WellyMCPTools']

__version__ = '0.1.0'
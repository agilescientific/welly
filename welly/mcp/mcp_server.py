#!/usr/bin/env python3
"""
Welly MCP Server

A Model Context Protocol server that provides AI assistants with access to
welly's petrophysical analysis capabilities.

Compatible with:
- Any MCP-compatible client
- Cursor IDE  

Usage:
    python -m welly.mcp
    python welly/mcp/mcp_server.py
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
)

from .tools import WellyMCPTools
from .session import SessionManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WellyMCPServer:
    """MCP Server for welly petrophysical analysis."""
    
    def __init__(self):
        self.server = Server("welly-mcp")
        self.session_manager = SessionManager()
        self.tools = WellyMCPTools(self.session_manager)
        
        # Register MCP handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools():
            """List available welly tools."""
            return [
                    Tool(
                        name="load_las_well",
                        description="Load a LAS (Log ASCII Standard) well log file containing petrophysical data. START HERE - this is typically the first step in well log analysis. LAS files contain depth measurements and well log curves like gamma ray (GR), resistivity (RT), density (RHOB), neutron porosity (NPHI), etc. Returns a well_id that you must save for all subsequent operations. Provide a file path on the filesystem, NOT file contents.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Absolute filesystem path to the LAS file. Examples: '/data/wells/WELL-001.las' or './logs/my_well.las'. Must be an existing file on disk - do NOT provide file contents or base64 data."
                                },
                                "alias_dict": {
                                    "type": "object", 
                                    "description": "Optional curve renaming dictionary. Example: {'GR': 'GAMMA_RAY', 'DEPT': 'MEASURED_DEPTH'} to standardize curve names during loading.",
                                    "additionalProperties": {"type": "string"}
                                }
                            },
                            "required": ["file_path"]
                        }
                    ),
                    Tool(
                        name="get_curve_stats",
                        description="Calculate statistical analysis for well log curves including mean, min, max, standard deviation, percentiles, and data quality metrics. Essential for understanding data ranges, identifying outliers, and assessing data quality before interpretation. Works on any loaded well - requires well_id from load_las_well().",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "well_id": {
                                    "type": "string",
                                    "description": "Unique well identifier returned by load_las_well(). Always use the exact well_id string from the load operation."
                                },
                                "curve_names": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional list of specific curve names to analyze. Example: ['GR', 'RHOB', 'NPHI']. If omitted, analyzes ALL curves in the well. Use list_curves() first to see available options."
                                }
                            },
                            "required": ["well_id"]
                        }
                    ),
                    Tool(
                        name="plot_well_log",
                        description="Generate professional well log plots with multiple curve tracks in industry-standard format. Automatically applies proper petrophysical scales (GR: 0-200 gAPI, density: 1.95-2.95 g/cm3, etc.) and colors. Creates high-resolution PNG images encoded as base64. Perfect for visualizing well data, comparing curves, and creating reports. Unknown curves auto-scale based on data range.",
                        inputSchema={
                            "type": "object", 
                            "properties": {
                                "well_id": {
                                    "type": "string",
                                    "description": "Unique well identifier returned by load_las_well(). Always use the exact well_id string from the load operation."
                                },
                                "curves": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional list of curve names to plot. Example: ['GR', 'RHOB', 'RT', 'NPHI']. If omitted, automatically plots first 6 curves. Each curve gets its own track with proper scaling."
                                },
                                "depth_range": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 2,
                                    "maxItems": 2,
                                    "description": "Optional depth zoom as [start_depth, end_depth]. Example: [2000.0, 2100.0] to plot 100-unit interval. Use well units (feet or meters). Omit to plot entire well."
                                }
                            },
                            "required": ["well_id"]
                        }
                    ),
                    Tool(
                        name="get_well_info",
                        description="Extract well header information and metadata from LAS files including well name, location coordinates, depth ranges, curve descriptions, and measurement units. Essential for well identification, understanding data context, and preparing analysis reports. Provides geographic info, data quality details, and measurement specifications.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "well_id": {
                                    "type": "string", 
                                    "description": "Unique well identifier returned by load_las_well(). Always use the exact well_id string from the load operation."
                                }
                            },
                            "required": ["well_id"]
                        }
                    ),
                    Tool(
                        name="list_curves",
                        description="List available well log curves with metadata including curve names (mnemonics), units, descriptions, data point counts, and null value indicators. Use this after loading a well to see what data is available before plotting or analysis. Common curves: GR (gamma ray), RHOB (density), NPHI (neutron), RT (resistivity), CAL (caliper), SP (spontaneous potential).",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "well_id": {
                                    "type": "string",
                                    "description": "Unique well identifier returned by load_las_well(). Always use the exact well_id string from the load operation."
                                }
                            },
                            "required": ["well_id"]
                        }
                    )
                ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls."""
            try:
                # Use a consistent session ID to maintain state across tool calls
                # This ensures wells loaded in one call are available in subsequent calls
                session_id = "default_session"
                
                if name == "load_las_well":
                    result = await self.tools.load_las_well(arguments, session_id)
                elif name == "get_curve_stats":
                    result = await self.tools.get_curve_stats(arguments, session_id)
                elif name == "plot_well_log":
                    result = await self.tools.plot_well_log(arguments, session_id)
                elif name == "get_well_info":
                    result = await self.tools.get_well_info(arguments, session_id)
                elif name == "list_curves":
                    result = await self.tools.list_curves(arguments, session_id)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Handle different return types
                if isinstance(result, dict) and "plot_base64" in result:
                    # Return plot as image
                    return [
                        TextContent(
                            type="text",
                            text=f"Generated well log plot. {result.get('message', '')}"
                        ),
                        ImageContent(
                            type="image",
                            data=result["plot_base64"],
                            mimeType="image/png"
                        )
                    ]
                else:
                    # Format as JSON for readability
                    if isinstance(result, dict):
                        text = json.dumps(result, indent=2)
                    else:
                        text = str(result)
                    
                    return [
                        TextContent(
                            type="text", 
                            text=text
                        )
                    ]
                    
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point for the MCP server."""
    server = WellyMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
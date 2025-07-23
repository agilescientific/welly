# Welly MCP server

A [Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/mcp) server for exposing welly's petrophysical analysis capabilities to AI assistants.

## Features

- **Load LAS files** - Import well log data for analysis
- **Statistical analysis** - Calculate curve statistics and summary information  
- **Well log plotting** - Generate publication-quality visualizations
- **Metadata extraction** - Access well header and curve information
- **Session management** - Maintain state across multiple operations

## Table of Contents

- [Welly MCP server](#welly-mcp-server)
  - [Features](#features)
  - [Table of Contents](#table-of-contents)
  - [Compatibility](#compatibility)
  - [Installation](#installation)
    - [From pip (when available)](#from-pip-when-available)
    - [Development install](#development-install)
  - [Usage](#usage)
    - [Standalone MCP Server](#standalone-mcp-server)
    - [Programmatic Usage](#programmatic-usage)
  - [Configuration for IDEs](#configuration-for-ides)
    - [Cursor IDE (VS Code fork)](#cursor-ide-vs-code-fork)
  - [Workflow](#workflow)
  - [Available Tools](#available-tools)
    - [`load_las_well`](#load_las_well)
    - [`get_curve_stats`](#get_curve_stats)
    - [`plot_well_log`](#plot_well_log)
    - [`get_well_info`](#get_well_info)
    - [`list_curves`](#list_curves)
    - [Why only 5 tools?](#why-only-5-tools)
    - [Potential Tools](#potential-tools)
  - [Example Workflow](#example-workflow)
  - [Common Issues \& Solutions](#common-issues--solutions)
  - [Development](#development)
    - [Project Structure](#project-structure)
    - [Testing](#testing)
  - [Contact](#contact)

## Compatibility

This MCP server works with:
- **Any MCP-compatible client**
- **Cursor IDE** - Code editor (VS Code fork) 

## Installation

### From pip (when available)
```bash
pip install welly[mcp]
```

### Development install 
```bash
git clone https://github.com/AlmazErmilov/welly-fork  # your fork or the original repo https://github.com/agilescientific/welly
cd welly-fork
# Install welly in development mode
pip install -e .
# Install MCP dependencies
pip install -r welly/mcp/requirements.txt
```

**Note for zsh users**: If using zsh shell, quote the brackets: `pip install -e ".[mcp]"`

## Usage

### Standalone MCP Server
```bash
# Run as classic MCP server (from welly-fork directory)
python -m welly.mcp

# Note: Direct execution (python welly/mcp/mcp_server.py) won't work due to relative imports
# Always use the module approach: python -m welly.mcp
```

### Programmatic Usage
```python
from welly.mcp import WellyMCPServer
import asyncio

async def run_server():
    server = WellyMCPServer()
    await server.run()

asyncio.run(run_server())
```

## Configuration for IDEs

### Cursor IDE (VS Code fork)

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP" or navigate to Extensions → MCP
3. Click "Edit in settings.json"
4. Add the following configuration:

```json
{
  "mcpServers": {
    "welly": {
      "command": "python",
      "args": ["-m", "welly.mcp"],
      "cwd": "/path/to/welly"
    }
  }
}
```

**Example with multiple MCP servers:**
```json
{
  "mcpServers": {
    "browser-tools": {
      "command": "npx @agentdeskai/browser-tools-mcp@latest"
    },
    "welly": {
      "command": "python",
      "args": ["-m", "welly.mcp"],
      "cwd": "/path/to/welly"
    }
  }
}
```

**Important Notes:**
- Replace `/path/to/welly` with the actual path to your welly directory
- Make sure you've installed welly in development mode: `pip install -e .`
- You can use the full Python path if needed: `"command": "/Users/username/anaconda3/bin/python"`
- Restart Cursor after making changes to the configuration

## Workflow

The welly MCP tools follow a session-based workflow:

1. **Load a well** - Always start by loading a LAS file using `load_las_well`
2. **Get the well_id** - The tool returns a unique `well_id` 
3. **Use the well_id** - Pass this `well_id` to other tools for analysis

This workflow ensures that wells remain in memory during your analysis session.

## Available Tools

### `load_las_well`
Load a LAS file and create a Well object for analysis.

**Parameters:**
- `file_path` (string, required): Path to the LAS file
- `alias_dict` (object, optional): Curve name mapping

**Important Notes:**
- The tool expects a file path, not file contents
- Supports LAS 1.2 and 2.0 formats (LAS 3.0 support planned)
- Handles wrapped LAS files automatically
- Returns a unique `well_id` that must be used for subsequent operations

**Example:**
```
Load the LAS file at /path/to/well.las
```

### `get_curve_stats`
Calculate statistical summary for curves in a loaded well.

**Parameters:**
- `well_id` (string, required): ID of the loaded well
- `curve_names` (array, optional): Specific curves to analyze

**Example:**
```
Calculate statistics for all curves in the loaded well
```

### `plot_well_log`
Generate a well log plot visualization.

**Parameters:**
- `well_id` (string, required): ID of the loaded well  
- `curves` (array, optional): Curves to include in plot
- `depth_range` (array, optional): [start, end] depth range

**Important Notes:**
- Returns base64-encoded PNG image for display
- Automatically limits to first 6 curves for readability if none specified
- Uses matplotlib with optimized settings for well log visualization

**Example:**
```
Plot GR, NPHI, and RHOB curves for the well
```

### `get_well_info`
Get header information and metadata from a loaded well.

**Parameters:**
- `well_id` (string, required): ID of the loaded well

### `list_curves`
List all available curves in a loaded well.

**Parameters:**
- `well_id` (string, required): ID of the loaded well

### Why only 5 tools?

Will be added more, let's say these 5 tools cover the most common and simple well log analysis for now:
- **Data Loading**: `load_las_well` handles LAS file import
- **Data Exploration**: `list_curves` and `get_well_info` help understand the data
- **Analysis**: `get_curve_stats` provides statistical analysis
- **Visualization**: `plot_well_log` creates publication-quality plots

Additional tools will be added later.

### Potential Tools

Based on welly's wide capabilities, future tools could include:

**Deviation & Trajectory Tools**
- `add_deviation_survey` - Add deviation data to compute 3D well trajectory
- `get_well_trajectory` - Extract well path coordinates (x, y, TVD)
- `plot_trajectory` - Generate plan view or 3D trajectory visualizations

**Data Export Tools**
- `export_to_dataframe` - Export curves to pandas DataFrame for analysis
- `export_to_matrix` - Export as numpy array for numerical processing
- `apply_curve_alias` - Standardize curve names using alias dictionaries

**Curve Manipulation Tools**
- `resample_curves` - Change sampling interval of curves
- `compute_curve` - Calculate new curves from existing ones (e.g., porosity from density)
- `smooth_curve` - Apply filters to reduce noise in log data

**Multi-Well Project Tools**
- `create_project` - Combine multiple wells for regional analysis
- `project_statistics` - Statistics across multiple wells
- `project_cross_plot` - Cross-plot parameters from different wells

**Quality Control Tools**
- `run_quality_checks` - Automated QC tests on well data
- `generate_qc_report` - Create HTML quality control reports
- `flag_bad_data` - Identify and flag suspicious data points

etc.

## Example Workflow

1. **Load a well**: "Load the LAS file at /data/well_001.las"
2. **Explore data**: "List all curves in the well"  
3. **Analyze**: "Calculate statistics for the GR and NPHI curves"
4. **Visualize**: "Create a well log plot showing GR, NPHI, and RHOB"
5. **Get details**: "Show me the well header information"

## Common Issues & Solutions

**"No tools enabled" in Cursor/Claude Desktop:**
- Verify the `cwd` path points to your welly-fork directory
- Test welly installation: `python -c "import welly; print('✅ Welly OK')"`
- Check MCP server starts: `python -m welly.mcp` (should wait silently for input)
- Restart IDE after configuration changes

**File path problems:**
- Use absolute paths: `/full/path/to/file.las` (not relative paths)
- MCP tools need file paths, not file contents or drag-and-drop
- Ensure file exists and has read permissions

**IDE import errors:**
- Install MCP: `pip install mcp` 
- Install welly: `pip install -e .` (from welly-fork root)
- Check Python interpreter in IDE settings
- Often cosmetic - code runs despite warnings

## Development

### Project Structure
```
welly/mcp/
├── __init__.py          # Module exports and version
├── __main__.py          # CLI entry point for python -m welly.mcp
├── mcp_server.py        # MCP server implementation with stdio protocol  
├── tools.py             # 5 core MCP tools (load, stats, plot, info, list)
├── session.py           # Session management for well state persistence
├── requirements.txt     # MCP dependencies (mcp, matplotlib, etc.)
├── pytest.ini          # Test configuration for async tests
├── tests/               # Test suite directory
│   ├── __init__.py      # Test module init
│   └── test_mcp_server.py # Test suite (11 tests)
└── README.md            # This documentation file
```

### Testing

The test suite covers MCP functionality with 11 tests:

**Test Categories:**
- **Server Tests** - MCP server creation and tool registration
- **Tool Tests** - All 5 MCP tools with real LAS files from welly's test assets
- **Workflow Tests** - Complete load → analyze → plot → export workflows  
- **Error Handling** - Invalid files, missing wells, bad parameters
- **Session Tests** - State management and well persistence

**Key Test Coverage:**
- LAS file loading
- Statistical analysis validation
- Plot generation with base64 encoding
- Session isolation and cleanup
- Error propagation and meaningful messages

```bash
# Run all tests (11 tests, should be ~2 seconds)
python -m pytest welly/mcp/tests/ -v

# From MCP directory  
cd welly/mcp && python -m pytest tests/ -v

# Specific test categories
python -m pytest welly/mcp/tests/ -k "test_load_las_well" -v
python -m pytest welly/mcp/tests/ -k "test_full_workflow" -v
```

## Contact

This MCP server is being developed by Almaz Ermilov as part of a little research for a paper for the Abu Dhabi International Petroleum Exhibition and Conference (ADIPEC) in autumn 2025.

- **GitHub**: [AlmazErmilov](https://github.com/AlmazErmilov)
- **Contact**:
  - `almaz.ermilov@gmail.com`
  - `almaz.ermilov@uit.no`
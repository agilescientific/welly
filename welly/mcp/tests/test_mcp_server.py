"""
Tests for welly MCP server
"""

import asyncio
import json
import os
import pytest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from welly.mcp.mcp_server import WellyMCPServer
from welly.mcp.tools import WellyMCPTools
from welly.mcp.session import SessionManager


class TestMCPServer:
    """Test the MCP server functionality"""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance"""
        return WellyMCPServer()
    
    @pytest.fixture
    def test_las_path(self):
        """Get path to test LAS file"""
        # Use welly's test assets
        test_file = Path(__file__).parent.parent.parent.parent / "tests" / "assets" / "1.las"
        if not test_file.exists():
            pytest.skip(f"Test LAS file not found: {test_file}")
        return str(test_file)
    
    def test_server_creation(self, server):
        """Test that server can be created"""
        assert server is not None
        assert server.server.name == "welly-mcp"
        assert server.session_manager is not None
        assert server.tools is not None
    
    def test_list_tools(self, server):
        """Test that tools are properly registered"""
        # The tools are registered when the server is created
        # We can't directly test the list_tools handler without running the full server
        # So we just verify the server was created with handlers
        assert hasattr(server.server, 'list_tools')
        assert hasattr(server.server, 'call_tool')


class TestMCPTools:
    """Test the MCP tools functionality"""
    
    @pytest.fixture
    def session_manager(self):
        """Create a test session manager"""
        return SessionManager()
    
    @pytest.fixture
    def tools(self, session_manager):
        """Create a test tools instance"""
        return WellyMCPTools(session_manager)
    
    @pytest.fixture
    def test_las_path(self):
        """Get path to test LAS file"""
        test_file = Path(__file__).parent.parent.parent.parent / "tests" / "assets" / "1.las"
        if not test_file.exists():
            pytest.skip(f"Test LAS file not found: {test_file}")
        return str(test_file)
    
    @pytest.mark.asyncio
    async def test_load_las_well(self, tools, test_las_path):
        """Test loading a LAS file"""
        args = {"file_path": test_las_path}
        session_id = "test_session"
        
        result = await tools.load_las_well(args, session_id)
        
        assert "well_id" in result
        assert "curves" in result
        assert "metadata" in result
        assert "message" in result
        assert len(result["curves"]) > 0
        assert result["metadata"]["total_curves"] == len(result["curves"])
    
    @pytest.mark.asyncio
    async def test_load_las_well_file_not_found(self, tools):
        """Test loading a non-existent LAS file"""
        args = {"file_path": "/nonexistent/file.las"}
        session_id = "test_session"
        
        with pytest.raises(Exception) as excinfo:
            await tools.load_las_well(args, session_id)
        
        assert "LAS file not found" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_load_las_well_invalid_extension(self, tools):
        """Test loading a file with wrong extension"""
        # Use __file__ as a real file that exists but has wrong extension
        args = {"file_path": __file__}  # This .py file
        session_id = "test_session"
        
        with pytest.raises(Exception) as excinfo:
            await tools.load_las_well(args, session_id)
        
        assert "must be a LAS file" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tools, test_las_path):
        """Test a complete workflow: load, list, stats, info"""
        session_id = "test_workflow"
        
        # 1. Load LAS file
        load_args = {"file_path": test_las_path}
        load_result = await tools.load_las_well(load_args, session_id)
        well_id = load_result["well_id"]
        
        assert well_id is not None
        
        # 2. List curves
        list_args = {"well_id": well_id}
        list_result = await tools.list_curves(list_args, session_id)
        
        assert "curves" in list_result
        assert len(list_result["curves"]) > 0
        
        # 3. Get curve statistics
        stats_args = {
            "well_id": well_id,
            "curve_names": load_result["curves"][:2]  # First 2 curves
        }
        stats_result = await tools.get_curve_stats(stats_args, session_id)
        
        assert "statistics" in stats_result
        assert len(stats_result["statistics"]) == 2
        
        # 4. Get well info
        info_args = {"well_id": well_id}
        info_result = await tools.get_well_info(info_args, session_id)
        
        assert "header" in info_result
        assert "curves" in info_result
        assert "location" in info_result
    
    @pytest.mark.asyncio
    async def test_plot_well_log(self, tools, test_las_path):
        """Test plotting well logs"""
        session_id = "test_plot"
        
        # Load well first
        load_args = {"file_path": test_las_path}
        load_result = await tools.load_las_well(load_args, session_id)
        well_id = load_result["well_id"]
        
        # Plot first 2 curves
        plot_args = {
            "well_id": well_id,
            "curves": load_result["curves"][:2]
        }
        plot_result = await tools.plot_well_log(plot_args, session_id)
        
        assert "plot_base64" in plot_result
        assert len(plot_result["plot_base64"]) > 0
        assert "plotted_curves" in plot_result
        assert len(plot_result["plotted_curves"]) == 2
    
    @pytest.mark.asyncio
    async def test_invalid_well_id(self, tools):
        """Test operations with invalid well_id"""
        session_id = "test_invalid"
        invalid_well_id = "nonexistent_well"
        
        # Test each operation with invalid well_id
        with pytest.raises(Exception) as excinfo:
            await tools.get_curve_stats({"well_id": invalid_well_id}, session_id)
        assert "not found in session" in str(excinfo.value)
        
        with pytest.raises(Exception) as excinfo:
            await tools.list_curves({"well_id": invalid_well_id}, session_id)
        assert "not found in session" in str(excinfo.value)
        
        with pytest.raises(Exception) as excinfo:
            await tools.get_well_info({"well_id": invalid_well_id}, session_id)
        assert "not found in session" in str(excinfo.value)
        
        with pytest.raises(Exception) as excinfo:
            await tools.plot_well_log({"well_id": invalid_well_id}, session_id)
        assert "not found in session" in str(excinfo.value)


class TestSessionManager:
    """Test the session management functionality"""
    
    @pytest.fixture
    def session_manager(self):
        """Create a test session manager"""
        return SessionManager()
    
    def test_session_creation(self, session_manager):
        """Test creating a session"""
        session_id = "test_session"
        session_manager.create_session(session_id)
        
        assert session_id in session_manager.sessions
        assert "wells" in session_manager.sessions[session_id]
    
    def test_store_and_get_well(self, session_manager):
        """Test storing and retrieving a well"""
        session_id = "test_session"
        well_id = "test_well_id"
        well_data = {"name": "Test Well", "data": {}}
        
        session_manager.store_well(session_id, well_id, well_data)
        retrieved_well = session_manager.get_well(session_id, well_id)
        
        assert retrieved_well == well_data
    
    def test_get_nonexistent_well(self, session_manager):
        """Test getting a well that doesn't exist"""
        result = session_manager.get_well("nonexistent_session", "nonexistent_well")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Session Management for Welly MCP Server

Handles storage and retrieval of Well objects and analysis state
across multiple MCP tool calls.
"""

import logging
import time
from typing import Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages session state for MCP tool calls."""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session or return existing one."""
        if session_id is None:
            session_id = str(uuid4())
            
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'wells': {},
                'created_at': time.time(),
                'last_accessed': time.time()
            }
            logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session['last_accessed'] = time.time()
            return session
        return None
    
    def store_well(self, session_id: str, well_id: str, well_obj: Any):
        """Store a Well object in session."""
        session = self.get_session(session_id)
        if session is None:
            session_id = self.create_session(session_id)
            session = self.sessions[session_id]
            
        session['wells'][well_id] = well_obj
        logger.info(f"Stored well {well_id} in session {session_id}")
    
    def get_well(self, session_id: str, well_id: str) -> Optional[Any]:
        """Retrieve a Well object from session."""
        session = self.get_session(session_id)
        if session and well_id in session['wells']:
            return session['wells'][well_id]
        return None
    
    def list_wells(self, session_id: str) -> list:
        """List all wells in a session."""
        session = self.get_session(session_id)
        if session:
            return list(session['wells'].keys())
        return []
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_accessed'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def clear_session(self, session_id: str):
        """Clear a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session."""
        session = self.get_session(session_id)
        if session:
            return {
                'session_id': session_id,
                'wells_count': len(session['wells']),
                'wells': list(session['wells'].keys()),
                'created_at': session['created_at'],
                'last_accessed': session['last_accessed']
            }
        return {}
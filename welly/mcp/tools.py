"""
Welly MCP Tools

Implements MCP (Model Context Protocol) tools for petrophysical analysis using welly.
These tools enable AI assistants to perform well log analysis through natural language.
"""

import base64
import io
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import welly components
from welly import Well, Project
import lasio

from .session import SessionManager

logger = logging.getLogger(__name__)

class WellyMCPTools:
    """MCP tools for welly petrophysical analysis."""
    
    def __init__(self, session_manager: SessionManager):
        """Initialize with session manager."""
        self.session_manager = session_manager
    
    def _extract_depth_info(self, well):
        """Extract depth information from well curves."""
        try:
            if not well.data:
                return {'start': None, 'stop': None, 'step': None}
            
            # Use curve properties for depth information
            first_curve = list(well.data.values())[0]
            
            return {
                'start': first_curve.start,
                'stop': first_curve.stop,
                'step': first_curve.step
            }
            
        except Exception:
            return {'start': None, 'stop': None, 'step': None}
    
    def _create_curve_legend(self, curve_names, well):
        """Create a dynamic legend for curve plotting using welly's alias system."""
        try:
            # Import striplog Legend (optional dependency)
            from striplog import Legend
        except ImportError:
            # If striplog not available, return None (no legend)
            return None
        
        # Import welly's alias dictionary
        from welly.defaults import ALIAS
        
        # Industry-standard-ish curve plotting parameters for petrophysical analysis
        # Colors based on common-ish industry practices, proper curve standartization planned for the near future
        curve_params = {
            # Gamma Ray - traditionally red/dark red in many displays
            'GR': {'color': '#DC143C', 'xlim': '0,200', 'xscale': 'linear', 'ls': '-'},
            
            # Resistivity curves - various shades of red/orange for log scale
            'RESD': {'color': '#FF0000', 'xlim': '0.2,2000', 'xscale': 'log'},  # Red
            'RESM': {'color': '#FF4500', 'xlim': '0.2,2000', 'xscale': 'log'},  # Orange red
            'RESS': {'color': '#FF6347', 'xlim': '0.2,2000', 'xscale': 'log'},  # Tomato
            'AT10': {'color': '#FF0000', 'xlim': '0.2,2000', 'xscale': 'log'}, # Red
            'AT20': {'color': '#FF4500', 'xlim': '0.2,2000', 'xscale': 'log'}, # Orange red  
            'AT30': {'color': '#FF6347', 'xlim': '0.2,2000', 'xscale': 'log'}, # Tomato
            'AT60': {'color': '#FF7F50', 'xlim': '0.2,2000', 'xscale': 'log'}, # Coral
            'AT90': {'color': '#FFA500', 'xlim': '0.2,2000', 'xscale': 'log'}, # Orange
            'ILD': {'color': '#FF0000', 'xlim': '0.2,2000', 'xscale': 'log'},  # Red
            'ILM': {'color': '#FF4500', 'xlim': '0.2,2000', 'xscale': 'log'},  # Orange red
            'RT': {'color': '#FF0000', 'xlim': '0.2,2000', 'xscale': 'log'},   # Red
            
            # Density - traditionally blue 
            'DENS': {'color': '#0000FF', 'xlim': '1.95,2.95', 'xscale': 'linear'},  # Blue
            'RHOB': {'color': '#0000FF', 'xlim': '1.95,2.95', 'xscale': 'linear'},  # Blue
            'RHOZ': {'color': '#4169E1', 'xlim': '1.95,2.95', 'xscale': 'linear'}, # Royal blue
            
            # Neutron Porosity - traditionally magenta/purple
            'PHIN': {'color': '#FF00FF', 'xlim': '-0.15,0.45', 'xscale': 'linear'}, # Magenta
            'PHID': {'color': '#DA70D6', 'xlim': '-0.15,0.45', 'xscale': 'linear'}, # Orchid
            'NPHI': {'color': '#FF00FF', 'xlim': '-0.15,0.45', 'xscale': 'linear'}, # Magenta
            'TNPH': {'color': '#BA55D3', 'xlim': '-0.15,0.45', 'xscale': 'linear'}, # Medium orchid
            
            # Sonic - purple shades
            'DT': {'color': '#800080', 'xlim': '40,140', 'xscale': 'linear'},   # Purple
            'DTCO': {'color': '#800080', 'xlim': '40,140', 'xscale': 'linear'}, # Purple
            'DTS': {'color': '#9370DB', 'xlim': '100,400', 'xscale': 'linear'}, # Medium purple
            'DTSM': {'color': '#9370DB', 'xlim': '100,400', 'xscale': 'linear'}, # Medium purple
            
            # Caliper - brown/tan colors
            'CAL': {'color': '#8B4513', 'xlim': '6,20', 'xscale': 'linear'},   # Saddle brown
            'CALI': {'color': '#8B4513', 'xlim': '6,20', 'xscale': 'linear'},  # Saddle brown
            'C1': {'color': '#A0522D', 'xlim': '6,20', 'xscale': 'linear'},    # Sienna
            'C2': {'color': '#CD853F', 'xlim': '6,20', 'xscale': 'linear'},    # Peru
            
            # SP (Spontaneous Potential) - black/dark colors
            'SP': {'color': '#000000', 'xlim': '-200,200', 'xscale': 'linear'}, # Black
            
            # Photoelectric Factor - orange shades
            'PEF': {'color': '#FFA500', 'xlim': '0,10', 'xscale': 'linear'},   # Orange
            'PE': {'color': '#FFA500', 'xlim': '0,10', 'xscale': 'linear'},    # Orange
            
            # Water Saturation - cyan/teal colors  
            'SW': {'color': '#00CED1', 'xlim': '0,1', 'xscale': 'linear'},     # Dark turquoise
            'SWT': {'color': '#48D1CC', 'xlim': '0,1', 'xscale': 'linear'},    # Medium turquoise
            
            # Bit Size - gray
            'BS': {'color': '#708090', 'xlim': '6,20', 'xscale': 'linear'},    # Slate gray
        }
        
        # Build legend CSV for curves present in the well
        legend_lines = ['colour,lw,ls,xlim,xscale,curve mnemonic']
        
        for curve_name in curve_names:
            # Find curve type using welly's alias system
            curve_type = None
            curve_upper = curve_name.upper()
            
            # Check each curve type in welly's ALIAS dictionary
            for standard_type, aliases in ALIAS.items():
                if curve_upper in aliases:
                    curve_type = standard_type
                    break
            
            # Get parameters for this curve type
            params = curve_params.get(curve_type, {})
            # Add default line style for recognized curves
            if params and 'ls' not in params:
                params = params.copy()
                params['ls'] = '-'
            
            if not params:
                # Default for unknown curves - calculate xlim from data
                try:
                    curve_data = well.data[curve_name]
                    if hasattr(curve_data, 'values'):
                        values = curve_data.values[~np.isnan(curve_data.values)]
                        if len(values) > 0:
                            data_min = float(np.nanmin(values))
                            data_max = float(np.nanmax(values))
                            # Add 5% padding for better visualization
                            padding = (data_max - data_min) * 0.05
                            xlim = f"{data_min - padding:.3f},{data_max + padding:.3f}"
                        else:
                            xlim = ''
                    else:
                        xlim = ''
                except:
                    xlim = ''
                
                # Default parameters for unrecognized curves
                unknown_colors = ['#191970', '#000080', '#483D8B', '#4682B4', '#4169E1', '#6495ED']
                color_index = hash(curve_name) % len(unknown_colors)
                color = unknown_colors[color_index]
                
                params = {'color': color, 'xlim': xlim, 'xscale': 'linear', 'ls': '--'}
            
            # Build CSV line
            color = params.get('color', '#666666')
            xlim = params.get('xlim', '')
            xscale = params.get('xscale', 'linear')
            ls = params.get('ls', '-')
            
            xlim_str = f'"{xlim}"' if xlim else ''
            line = f'{color},1.0,{ls},{xlim_str},{xscale},{curve_name}'
            legend_lines.append(line)
        
        # Create legend from CSV
        legend_csv = '\n'.join(legend_lines)
        
        try:
            return Legend.from_csv(text=legend_csv)
        except Exception:
            # If legend creation fails, return None
            return None
    
    async def load_las_well(self, args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Load a LAS (Log ASCII Standard) file containing well log data.
        
        This is typically the FIRST step in well log analysis. LAS files contain:
        - Depth/time measurements
        - Well log curves (GR, resistivity, porosity, etc.)
        - Well header information (location, name, etc.)
        
        Args:
            args: Dictionary with required and optional parameters:
                - file_path (str, required): Absolute path to LAS file on filesystem
                  Examples: "/path/to/well.las", "./data/my_well.las"
                  NOTE: Must be actual file path, not file contents
                - alias_dict (dict, optional): Rename curves during loading
                  Example: {"GR": "GAMMA_RAY", "DEPT": "DEPTH"}
            session_id: Session identifier for data persistence
            
        Returns:
            Dictionary with loaded well information:
                - well_id (str): Unique ID for this well - SAVE THIS for other operations
                - curves (list): Available curve names like ["GR", "RHOB", "NPHI"]
                - metadata (dict): Well info including name, depth range, location
                - message (str): Success confirmation
                
        Typical Usage Pattern:
            1. load_las_well() -> get well_id
            2. list_curves() -> see available data  
            3. plot_well_log() or get_curve_stats() -> analyze data
                
        Example:
            load_las_well({
                "file_path": "/data/wells/WELL-001.las",
                "alias_dict": {"GR": "GAMMA_RAY"}  # optional renaming
            }, "session_123")
        """
        try:
            file_path = args['file_path']
            alias_dict = args.get('alias_dict', {})
            
            # Validate file exists and is readable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"LAS file not found: {file_path}")
            
            if not file_path.lower().endswith('.las'):
                raise ValueError("File must be a LAS file (.las extension)")
            
            # Load LAS file using welly
            well = Well.from_las(file_path, alias=alias_dict)
            
            # Generate unique well ID
            well_id = str(uuid.uuid4())
            
            # Store in session
            self.session_manager.store_well(session_id, well_id, well)
            
            # Get curve information
            curves = list(well.data.keys()) if well.data else []
            
            # Extract basic metadata (handle different welly API versions)
            metadata = {
                'well_name': getattr(well, 'name', 'Unknown'),
                'location': {
                    'x': getattr(well.location, 'x', None) if hasattr(well, 'location') and well.location else None,
                    'y': getattr(well.location, 'y', None) if hasattr(well, 'location') and well.location else None
                },
                'start_depth': None,
                'stop_depth': None, 
                'step_size': None,
                'total_curves': len(curves)
            }
            
            # Extract depth information
            depth_info = self._extract_depth_info(well)
            metadata.update({
                'start_depth': depth_info['start'],
                'stop_depth': depth_info['stop'],
                'step_size': depth_info['step']
            })
            
            result = {
                'well_id': well_id,
                'curves': curves,
                'metadata': metadata,
                'message': f"Successfully loaded LAS file: {Path(file_path).name}"
            }
            
            logger.info(f"Loaded well {well_id} with {len(curves)} curves")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load LAS file: {e}")
            raise Exception(f"Error loading LAS file: {str(e)}")
    
    async def get_curve_stats(self, args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Calculate statistical analysis for well log curves.
        
        Provides statistics including:
        - Basic stats: mean, min, max, standard deviation
        - Percentiles: 25th, 50th (median), 75th
        - Data quality: count of valid points, null values
        - Units of measurement for each curve
        
        Args:
            args: Dictionary with analysis parameters:
                - well_id (str, required): Well ID from load_las_well()
                - curve_names (list, optional): Specific curves to analyze
                  If not specified: analyzes ALL curves in the well
                  Example: ["GR", "RHOB", "NPHI"]
            session_id: Session identifier
            
        Returns:
            Dictionary with statistical results:
                - statistics (dict): Per-curve stats with keys like:
                  - count: number of valid data points
                  - mean, min, max: basic statistics
                  - std: standard deviation
                  - median: 50th percentile  
                  - percentile_25, percentile_75: quartiles
                  - null_count: missing/invalid values
                  - unit: measurement units (gAPI, ohm-m, etc.)
                - analyzed_curves (list): curves that were processed
                - message (str): summary of analysis
                
        Useful For:
            - Data quality assessment
            - Identifying outliers or data issues
            - Understanding curve value ranges
            - Petrophysical interpretation preparation
                
        Example:
            get_curve_stats({
                "well_id": "abc-123-def",
                "curve_names": ["GR", "RHOB"]  # optional selection
            }, "session_123")
        """
        try:
            well_id = args['well_id']
            curve_names = args.get('curve_names', None)
            
            # Retrieve well from session
            well = self.session_manager.get_well(session_id, well_id)
            if well is None:
                raise ValueError(f"Well {well_id} not found in session {session_id}")
            
            # Determine curves to analyze
            if curve_names is None:
                curve_names = list(well.data.keys())
            else:
                # Validate requested curves exist
                available_curves = list(well.data.keys())
                invalid_curves = [c for c in curve_names if c not in available_curves]
                if invalid_curves:
                    raise ValueError(f"Curves not found: {invalid_curves}. Available: {available_curves}")
            
            stats_result = {}
            
            for curve_name in curve_names:
                curve = well.data[curve_name]
                
                try:
                    # Get curve statistics
                    stats_df = curve.describe()
                    curve_stats = stats_df[curve_name].to_dict()
                    
                    # Convert to our expected format with additional metadata
                    stats = {
                        'count': int(curve_stats['count']),
                        'mean': float(curve_stats['mean']),
                        'std': float(curve_stats['std']),
                        'min': float(curve_stats['min']),
                        'max': float(curve_stats['max']),
                        'median': float(curve_stats['50%']),  # median is 50th percentile
                        'percentile_25': float(curve_stats['25%']),
                        'percentile_75': float(curve_stats['75%']),
                        'null_count': len(curve.values) - int(curve_stats['count']),
                        'unit': getattr(curve, 'units', 'unknown')
                    }
                    
                except Exception:
                    # Fallback to basic statistics
                    basic_stats = curve.get_stats()
                    stats = {
                        'count': basic_stats.get('samples', 0),
                        'mean': basic_stats.get('mean', None),
                        'min': basic_stats.get('min', None),
                        'max': basic_stats.get('max', None),
                        'null_count': basic_stats.get('nulls', 0),
                        'unit': getattr(curve, 'units', 'unknown'),
                        'message': 'Limited statistics available'
                    }
                
                stats_result[curve_name] = stats
            
            result = {
                'well_id': well_id,
                'statistics': stats_result,
                'analyzed_curves': curve_names,
                'message': f"Statistical analysis completed for {len(curve_names)} curves"
            }
            
            logger.info(f"Calculated statistics for {len(curve_names)} curves in well {well_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate curve statistics: {e}")
            raise Exception(f"Error calculating statistics: {str(e)}")
    
    async def plot_well_log(self, args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Generate a professional well log plot with multiple curve tracks.
        
        Creates industry-standard well log visualization with:
        - Professional petrophysical scales (GR: 0-200 gAPI, etc.)
        - Proper curve colors and scaling
        - Depth track with measured depth reference
        - Auto-scaling for unknown curves
        
        Args:
            args: Dictionary with plotting parameters:
                - well_id (str, required): Well ID from load_las_well()
                - curves (list, optional): Curve names to plot
                  If not specified: plots first 6 curves automatically
                  Example: ["GR", "RHOB", "NPHI", "RT"]
                - depth_range (list, optional): [start_depth, end_depth] in well units
                  Example: [2000.0, 2100.0] to plot 100ft/30m interval
            session_id: Session identifier
            
        Returns:
            Dictionary with plot data:
                - plot_base64 (str): PNG image encoded as base64 string
                - plotted_curves (list): Names of curves actually plotted
                - depth_range (list): Actual depth range plotted
                - message (str): Success message
                
        Usage Tips:
            - Images are high-resolution (150 DPI) PNG format
            - Each curve gets its own track with professional scaling
            - Unknown curves auto-scale based on data min/max
            - Display base64 image in web browsers or decode to file
                
        Example:
            plot_well_log({
                "well_id": "abc-123-def",
                "curves": ["GR", "RHOB", "NPHI"],
                "depth_range": [1500.0, 1600.0]  # optional zoom
            }, "session_123")
        """
        try:
            well_id = args['well_id']
            curve_names = args.get('curves', None)
            depth_range = args.get('depth_range', None)
            
            # Retrieve well from session
            well = self.session_manager.get_well(session_id, well_id)
            if well is None:
                raise ValueError(f"Well {well_id} not found in session {session_id}")
            
            # Determine curves to plot
            if curve_names is None:
                curve_names = list(well.data.keys())
                # Limit to first 6 curves for readability
                curve_names = curve_names[:6]
            
            # Validate curves exist
            available_curves = list(well.data.keys())
            invalid_curves = [c for c in curve_names if c not in available_curves]
            if invalid_curves:
                raise ValueError(f"Curves not found: {invalid_curves}. Available: {available_curves}")
            
            # Prepare tracks for welly plotting
            # Include MD track for depth reference, as shown in tutorial
            tracks = ['MD'] + curve_names
            
            # Apply depth filtering if specified
            if depth_range and len(depth_range) == 2:
                start_depth, end_depth = depth_range
                extents = (start_depth, end_depth)
            else:
                # Use 'curves' to show full extent of data
                extents = 'curves'
            
            # Create a dynamic legend for professional curve plotting
            legend = self._create_curve_legend(curve_names, well)
            
            # Use welly's plot_well function for proper legend support
            # well.plot() method doesn't apply legend correctly, but plot_well() function does
            from welly.plot import plot_well
            fig = plot_well(
                well=well,
                tracks=tracks,
                extents=extents,
                legend=legend
            )
            
            # Set figure size for better readability
            if fig:
                fig.set_size_inches(max(12, len(curve_names) * 2), 10)
            
            # Convert plot to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            result = {
                'well_id': well_id,
                'plot_base64': plot_base64,
                'plotted_curves': curve_names,
                'depth_range': depth_range,
                'message': f"Generated well log plot with {len(curve_names)} curves"
            }
            
            logger.info(f"Generated plot for well {well_id} with curves: {curve_names}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate plot: {e}")
            raise Exception(f"Error generating plot: {str(e)}")
    
    async def get_well_info(self, args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Extract well header information and metadata.
        
        Retrieves available well information from LAS file headers including:
        - Well identification and naming
        - Geographic location coordinates
        - Depth/time measurement details
        - Curve metadata and descriptions
        
        Args:
            args: Dictionary with request parameters:
                - well_id (str, required): Well ID from load_las_well()
            session_id: Session identifier
            
        Returns:
            Dictionary with well information:
                - header (dict): LAS file header sections containing:
                  - Well section: well name, location, dates
                  - Version section: LAS file version info
                  - Parameter section: additional well parameters
                - curves (dict): Per-curve metadata with units and descriptions
                - location (dict): Geographic information:
                  - x, y: coordinates (if available)
                  - kb: kelly bushing elevation
                  - crs: coordinate reference system
                - depth_info (dict): Measurement details:
                  - start_depth, stop_depth: well extent
                  - step_size: measurement interval
                - message (str): retrieval summary
                
        Useful For:
            - Well identification and documentation
            - Understanding coordinate systems and projections
            - Checking data quality and completeness
            - Preparing reports and analysis summaries
                
        Example:
            get_well_info({
                "well_id": "abc-123-def"
            }, "session_123")
        """
        try:
            well_id = args['well_id']
            
            # Retrieve well from session
            well = self.session_manager.get_well(session_id, well_id)
            if well is None:
                raise ValueError(f"Well {well_id} not found in session {session_id}")
            
            # Extract header information
            header_info = {}
            if hasattr(well, 'header') and well.header is not None:
                try:
                    # Handle DataFrame header
                    if hasattr(well.header, 'to_dict'):
                        header_info = well.header.to_dict()
                    else:
                        # Handle dict-like header
                        for section, data in well.header.items():
                            if isinstance(data, dict):
                                header_info[section] = dict(data)
                            else:
                                header_info[section] = str(data)
                except Exception:
                    header_info = {'error': 'Could not parse header information'}
            
            # Get curve information
            curves_info = {}
            if well.data:
                for curve_name, curve in well.data.items():
                    curves_info[curve_name] = {
                        'units': getattr(curve, 'units', 'unknown'),
                        'description': getattr(curve, 'description', ''),
                        'data_points': len(curve.values) if hasattr(curve, 'values') else len(curve)
                    }
            
            # Location information
            location_info = {}
            if hasattr(well, 'location') and well.location is not None:
                location_info = {
                    'x': getattr(well.location, 'x', None),
                    'y': getattr(well.location, 'y', None),
                    'kb': getattr(well.location, 'kb', None),
                    'crs': str(getattr(well.location, 'crs', 'unknown'))
                }
            
            result = {
                'well_id': well_id,
                'header': header_info,
                'curves': curves_info,
                'location': location_info,
                'depth_info': self._extract_depth_info(well),
                'message': f"Retrieved information for well {well_id}"
            }
            
            logger.info(f"Retrieved info for well {well_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get well info: {e}")
            raise Exception(f"Error getting well info: {str(e)}")
    
    async def list_curves(self, args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        List available well log curves with metadata.
        
        Provides inventory of curves in the loaded well including:
        - Curve names and descriptions
        - Units of measurement
        - Data point counts
        - Null value indicators
        
        Args:
            args: Dictionary with query parameters:
                - well_id (str, required): Well ID from load_las_well()
            session_id: Session identifier
            
        Returns:
            Dictionary with curve inventory:
                - curves (list): List of curve objects, each containing:
                  - name (str): curve mnemonic (e.g., "GR", "RHOB")
                  - units (str): measurement units (e.g., "gAPI", "g/cm3")
                  - description (str): curve description
                  - data_points (int): number of measurements
                  - has_nulls (bool): whether curve contains missing values
                - total_curves (int): count of available curves
                - message (str): summary message
                
        Typical Usage:
            - After loading well, to see what data is available
            - Before plotting or analysis, to select appropriate curves
            - For data inventory and quality assessment
                
        Common Curve Types:
            - GR: Gamma Ray (gAPI)
            - RHOB/DENS: Bulk Density (g/cm3)
            - NPHI/PHIN: Neutron Porosity (fraction)
            - RT/RESD: Deep Resistivity (ohm-m)
            - CAL: Caliper (inches)
                
        Example:
            list_curves({
                "well_id": "abc-123-def"
            }, "session_123")
        """
        try:
            well_id = args['well_id']
            
            # Retrieve well from session
            well = self.session_manager.get_well(session_id, well_id)
            if well is None:
                raise ValueError(f"Well {well_id} not found in session {session_id}")
            
            # Get curve names and details
            curves = []
            if well.data:
                for curve_name, curve in well.data.items():
                    curve_info = {
                        'name': curve_name,
                        'units': getattr(curve, 'units', 'unknown'),
                        'description': getattr(curve, 'description', ''),
                        'data_points': len(curve.values) if hasattr(curve, 'values') else len(curve),
                        'has_nulls': bool(np.isnan(curve.values).any()) if hasattr(curve, 'values') else False
                    }
                    curves.append(curve_info)
            
            result = {
                'well_id': well_id,
                'curves': curves,
                'total_curves': len(curves),
                'message': f"Found {len(curves)} curves in well {well_id}"
            }
            
            logger.info(f"Listed {len(curves)} curves for well {well_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list curves: {e}")
            raise Exception(f"Error listing curves: {str(e)}")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import PathPatch
from matplotlib.ticker import AutoMinorLocator


def curve_info(w, verbose=True, return_dict=False):
    """For a Welly well, print curve name, units and descriptions
    Args
    ----
        w: Welly.Well
    Kwargs
    ------
        verbose: bool, prints out CURVE NAME, UNIT, DESCRIPTION for each curve in w if True
        
    Return
    ------
        curve_info: dict{CURVE_NAME: {CURVE:UNITS, CURVE:DESCRIPTION}}
    """
    curve_info = {}
    for curve in w.data.keys():
        text = f"Curve: {curve:>6}\tUnit: {w.data[curve].units:>5}\tDescr: {' '.join(w.data[curve].description.split())}"
        curve_info[curve] = {'UNITS': w.data[curve].units,
                             'DESCRIPTION': ' '.join(w.data[curve].description.split()),
                            }
        if verbose:
            print(text)
    if return_dict:
        return curve_info
    else:
        return None


def is_first_track(track, tracks):
    """Check if track is first in tracks list.
    Args
    ----
        track: str, name of track
        tracks: list, list of `track` objects
    Return
    ------
        bool
    """
    if track not in tracks:
        raise AssertionError('`track` not found in `tracks`')
    return True if tracks.index(track) == 0 else False


def make_axes(tracklist, figsize=(9, 6)):
    """Create the axes for a given tracklist.
    Args
    ----
        tracklist: `list` of `list` in the form `[['log1'],['log2', 'log3'],['log4']]`
        
    Return
    ------
        axs: `list` of Axes of type 'matplotlib.axes._subplots.AxesSubplot'
    """
    fig = plt.figure(constrained_layout=True, figsize=figsize)
    spec = gridspec.GridSpec(ncols=len(tracklist), nrows=1, figure=fig)
    axs, col_id = [], 0
    
    for track in tracklist:
        for curve in track:
            if col_id == 0 and is_first_track(curve, track):
                axs.append(fig.add_subplot(spec[0, col_id], label=col_id))
                col_id += 1
            elif is_first_track(curve, track):
                axs.append(fig.add_subplot(spec[0, col_id], sharey=axs[0], label=col_id))
                col_id += 1
            else:
                axs.append(axs[-1].twiny())
            
    return fig, axs


def fill_const_to_curve(ax, w, curve, top, base, const=0, color='k', **kwargs):
    """Fill from a constant to a curve with a given color.
    Args
    ----
        ax: matplotlib.axes._subplots.AxesSubplot object to plot into
        w: welly.well.Well object
        curve: welly.curve.Curve object, curve up to which to fill
        top: float-like, top of the interval
        base: float-like, base of the interval
        
    Kwargs
    ------
        const: float-like, value from which to fill
        color: a valid matplotlib color to fill with
        **kwargs: All other keyword arguments are passed on to `.PolyCollection`.
    Return
    ------
        None
    """
    ax.fill_betweenx(w.survey_basis()[(top <= w.survey_basis()) & (w.survey_basis() <= base)],
                     const,
                     w.data[curve].to_basis(start=top, stop=base).values,
                     where=w.data[curve].to_basis(start=top, stop=base).values > const,
                     color=color, **kwargs)
    return None


def fill_curve_vals_to_curve(ax, w, curve, top, base, xticks_max, side='right', cmap='YlOrBr', **kwargs):
    """Fill a track from an edge to a curve with a colorfill mapped to the curve value.
    Args
    ----
        ax: matplotlib.axes._subplots.AxesSubplot object to plot into
        w: welly.well.Well object
        curve: welly.curve.Curve object, curve up to which to fill
        top: float-like, top interval to fill to
        base: float-like, base interval to fill to
        xticks_max: float-like, max value of xticks
        
    Kwargs
    ------
        side: one of {`left`, `right`}, side of the track to fill relative to the curve
        cmap: a valid matplotlib color
        **kwargs: All other keyword arguments are passed on to `.PolyCollection`.
        
    Return
    ------
        None
    """
    arr = np.tile(w.data[curve].to_basis(start=top, stop=base).values, (xticks_max, 1)).T
    im = ax.imshow(arr, extent=[0, xticks_max, base, top], cmap=cmap, aspect='auto', origin='upper')
    curve_values = w.data[curve].to_basis(start=top, stop=base).values
    if side == 'right':
        paths = ax.fill_betweenx(y=w.survey_basis()[(top <= w.survey_basis()) 
                                                    & (w.survey_basis() <= base)],
                                 x1=0, x2=curve_values, color='w', **kwargs)
    else:
        paths = ax.fill_betweenx(y=w.survey_basis()[(top <= w.survey_basis()) 
                                                    & (w.survey_basis() <= base)],
                                 x1=curve_values, x2=xticks_max, color='w', **kwargs)
    return None


def fill_between_curves(ax, w, curve1, curve2, curve1_xlims, curve2_xlims, 
                        top, base, color1='grey', color2='yellow', **kwargs):
    """Fill a track from one curve to another based on crossover.
    Args
    ----
        ax: matplotlib.axes._subplots.AxesSubplot object to plot into
        w: welly.well.Well object
        curve1: str, name of welly.curve.Curve object, for example 'RHOB' 
        curve2: str, name of welly.curve.Curve object, for example 'NPHI' 
        curve1_xlims: xlims tuple
        curve2_xlims: xlims tuple
        top: float-like, top interval to fill to
        base: float-like, base interval to fill to
    
    Kwargs
    ------
        color1: matplotlib color for the first fill
        color2: matplotlib color for the second fill
        **kwargs: All other keyword arguments are passed on to `.PolyCollection`.
    
    Return
    ------
        None
    
    Reference
    ---------
    https://towardsdatascience.com/enhancing-visualization-of-well-logs-with-plot-fills-72d9dcd10c1b
    """
    depth = w.survey_basis()[(top <= w.survey_basis()) & (w.survey_basis() <= base)]
    curve1 = w.data[curve1].to_basis(start=top, stop=base).values
    curve2 = w.data[curve2].to_basis(start=top, stop=base).values
    nz=(((curve2 - np.max(curve2_xlims)) /
        (np.min(curve2_xlims) - np.max(curve2_xlims))) *
        (np.max(curve1_xlims) - np.min(curve1_xlims)) +
        np.min(curve1_xlims))

    ax.fill_betweenx(depth, curve1, nz, where=curve1>=nz, interpolate=True, color=color1, **kwargs)
    ax.fill_betweenx(depth, curve1, nz, where=curve1<=nz, interpolate=True, color=color2, **kwargs)
    
    return None

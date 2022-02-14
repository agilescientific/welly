"""
Module for plotting projects, wells and curves

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as ticker
from matplotlib.patches import PathPatch

from . import utils


class WellPlotError(Exception):
    """
    Generic error class.
    """
    pass


def plot_kdes_project(project,
                      mnemonic,
                      alias=None,
                      uwi_regex=None):
    """
    Plot KDEs for all curves with the given name.

    Args:
        project (welly.project.Project): Project object
        menemonic (str): the name of the curve to look for.
        alias (dict): a welly alias dictionary. e.g. {'density': ['DEN', 'DENS']}
        uwi_regex (str): a regex pattern. Only this part of the UWI will be displayed
            on the plot of KDEs.

    Returns:
        None or figure.
    """
    wells = project.filter_wells_by_data([mnemonic], alias=alias)
    fig, axs = plt.subplots(len(project), 1, figsize=(10, 1.5 * len(project)))

    # get all curves
    curves = [w.get_curve(mnemonic, alias=alias) for w in wells]

    # get curve data as np arrays
    curves = [curve.df.values for curve in curves]

    # remove nans
    all_data = np.hstack(curves)
    all_data = all_data[~np.isnan(all_data)]

    # Find values for common axis to exclude outliers.
    amax = np.percentile(all_data, 99)
    amin = np.percentile(all_data, 1)

    for i, w in enumerate(project):
        c = w.get_curve(mnemonic, alias=alias)

        if uwi_regex is not None:
            label = re.sub(uwi_regex, r'\1', w.uwi)
        else:
            label = w.uwi

        if c is not None:
            axs[i] = c.plot_kde(ax=axs[i], amax=amax, amin=amin, label=label + '-' + str(c.mnemonic))
        else:
            continue

    plt.close()
    return fig


def plot_map_project(project,
                     fields=('x', 'y'),
                     ax=None,
                     label=None,
                     width=6):
    """
    Plot a map of the wells in the project.

    Args:
        project (welly.project.Project): Project object
        fields (list): The two fields of the `location` object to use
            as the x and y coordinates. Default: `('x', 'y')`
        ax (matplotlib.axes.Axes): An axes object to plot into. Will be
            returned. If you don't pass one, we'll create one and give
            back the `fig` that it's in.
        label (str): The field of the `Well.header` object to use as the label.
            Default: `Well.header.name`.
        width (float): The width, in inches, of the plot. Default: 6 in.

    Returns:
        matplotlib.figure.Figure, or matplotlib.axes.Axes if you passed in
            an axes object as `ax`.
    """
    xattr, yattr = fields
    xys = np.array([[getattr(w.location, xattr), getattr(w.location, yattr)] for w in project])

    if ax is None:
        fig, ax = plt.subplots(figsize=(1 + width, width / utils.aspect(xys)))

    ax.scatter(*xys.T, s=60)
    ax.axis('equal')
    ax.grid(which='both', axis='both', color='k', alpha=0.2)

    if label:
        labels = [getattr(w.header, label) for w in project]
        for xy, label in zip(xys, labels):
            ax.annotate(label, xy + 1000, color='gray')

    return ax


def plot_depth_track_well(well,
                          ax,
                          md,
                          kind='MD',
                          tick_spacing=100):
    """
    Depth track plotting for well.

    Args:
        well (welly.well.Well): Well object.
        ax (ax): A matplotlib axis.
        md (ndarray): The measured depths of the track.
        kind (str): The kind of track to plot.

    Returns:
        ax.
    """
    if kind == 'MD':
        ax.set_yscale('bounded', vmin=md.min(), vmax=md.max())
    elif kind == 'TVD':
        tvd = well.location.md2tvd(md)
        ax.set_yscale('piecewise', x=tvd, y=md)
    else:
        raise Exception("Kind must be MD or TVD")

    ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))

    for sp in ax.spines.values():
        sp.set_color('gray')

    if ax.get_subplotspec().is_first_col():
        pad = -10
        ax.spines['left'].set_color('none')
        ax.yaxis.set_ticks_position('right')
        for label in ax.get_yticklabels():
            label.set_horizontalalignment('right')
    elif ax.get_subplotspec().is_last_col():
        pad = -10
        ax.spines['right'].set_color('none')
        ax.yaxis.set_ticks_position('left')
        for label in ax.get_yticklabels():
            label.set_horizontalalignment('left')
    else:
        pad = -30
        for label in ax.get_yticklabels():
            label.set_horizontalalignment('center')

    ax.tick_params(axis='y', colors='gray', labelsize=12, pad=pad)
    ax.set_xticks([])

    ax.set(xticks=[])
    ax.depth_track = True

    return ax


def plot_well(well,
              legend=None,
              tracks=None,
              track_titles=None,
              alias=None,
              basis=None,
              extents='td',
              **kwargs):
    """
    Plot multiple tracks.

    Args:
        well (welly.well.Well): Well object.
        legend (striplog.legend): A legend instance.
        tracks (list): A list of strings and/or lists of strings. The
            tracks you want to plot from ``data``. Optional, but you will
            usually want to give it.
        track_titles (list): Optional. A list of strings and/or lists of
            strings. The names to give the tracks, if you don't want welly
            to guess.
        alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        basis (ndarray): Optional. The basis of the plot, if you don't
            want welly to guess (probably the best idea).
        extents (str): What to use for the y limits:
            'td' — plot 0 to TD.
            'curves' — use a basis that accommodates all the curves.
            'all' — use a basis that accommodates everything.
            (tuple) — give the upper and lower explictly.

    Returns:
        None. The plot is a side-effect.
    """
    # These will be treated differently.
    depth_tracks = ['MD', 'TVD']

    # Set tracks to 'all' if it's None.
    tracks = tracks or list(well.data.keys())
    track_titles = track_titles or tracks

    # Check that there is at least one curve.
    if well.count_curves(tracks, alias=alias) == 0:
        if alias:
            a = " with alias dict applied "
        else:
            a = " "
        m = "Track list{}returned no curves.".format(a)
        raise WellPlotError(m)

    # Figure out limits
    if basis is None:
        basis = well.survey_basis(keys=tracks, alias=alias)

    if extents == 'curves':
        upper, lower = basis[0], basis[-1]
    elif extents == 'td':
        try:
            upper, lower = 0, well.location.td
        except:
            m = "Could not read well.location.td, try extents='curves'"
            raise WellPlotError(m)
        if not lower:
            lower = basis[-1]
    elif extents == 'all':
        raise NotImplementedError("You cannot do that yet.")
    else:
        try:
            upper, lower = extents
        except:
            upper, lower = basis[0], basis[-1]

    # Figure out widths because we can't us gs.update() for that.
    widths = [0.4 if t in depth_tracks else 1.0 for t in tracks]

    # Set up the figure.
    ntracks = len(tracks)
    fig = plt.figure(figsize=(2 * ntracks, 12), facecolor='w')
    fig.suptitle(well.name, size=16, zorder=100,
                 bbox=dict(facecolor='w', alpha=1.0, ec='none'))
    gs = mpl.gridspec.GridSpec(1, ntracks, width_ratios=widths)

    # Tick spacing
    order_of_mag = np.round(np.log10(lower - upper))
    ts = 10 ** order_of_mag / 100

    # Plot first axis.
    # kwargs = {}
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.depth_track = False
    track = tracks[0]
    if '.' in track:
        track, kwargs['field'] = track.split('.')
    if track in depth_tracks:
        ax0 = plot_depth_track_well(well=well, ax=ax0, md=basis, kind=track, tick_spacing=ts)
    else:
        try:  # ...treating as a plottable object.
            ax0 = well.get_curve(track, alias=alias).plot(ax=ax0, legend=legend, **kwargs)
        except AttributeError:  # ...it's not there.
            pass
        except TypeError:  # ...it's a list.
            for t in track:
                try:
                    ax0 = well.get_curve(t, alias=alias).plot(ax=ax0, legend=legend, **kwargs)
                except AttributeError:  # ...it's not there.
                    pass
    tx = ax0.get_xticks()
    ax0.set_xticks(tx[1:-1])
    ax0.set_title(track_titles[0])

    # Plot remaining axes.
    for i, track in enumerate(tracks[1:]):
        # kwargs = {}
        ax = fig.add_subplot(gs[0, i + 1])
        ax.depth_track = False
        if track in depth_tracks:
            ax = plot_depth_track_well(well=well, ax=ax, md=basis, kind=track, tick_spacing=ts)
            continue
        if '.' in track:
            track, kwargs['field'] = track.split('.')
        plt.setp(ax.get_yticklabels(), visible=False)
        try:  # ...treating as a plottable object.
            curve = well.get_curve(track, alias=alias)
            curve._alias = track  # So that can retrieve alias from legend too.
            ax = curve.plot(ax=ax, legend=legend, **kwargs)
        except AttributeError:  # ...it's not there.
            continue
        except TypeError:  # ...it's a list.
            for t in track:
                if '.' in t:
                    track, kwargs['field'] = track.split('.')
                try:
                    curve = well.get_curve(t, alias=alias)
                    curve._alias = t
                    ax = curve.plot(ax=ax, legend=legend, **kwargs)
                except AttributeError:
                    continue
                except KeyError:
                    continue

        tx = ax.get_xticks()
        ax.set_xticks(tx[1:-1])
        ax.set_title(track_titles[i + 1])

    # Set sharing.
    axes = fig.get_axes()
    utils.sharey(axes)
    axes[0].set_ylim([lower, upper])

    # Adjust the grid.
    gs.update(wspace=0)

    # Adjust spines and ticks for non-depth tracks.
    for ax in axes:
        if not ax.depth_track:
            ax.set(yticks=[])
            ax.autoscale(False)
            ax.yaxis.set_ticks_position('none')
            ax.spines['top'].set_visible(True)
            ax.spines['bottom'].set_visible(True)
            for sp in ax.spines.values():
                sp.set_color('gray')

    plt.close()
    return fig


def plot_2d_curve(curve,
                  ax=None,
                  width=None,
                  aspect=60,
                  cmap=None,
                  plot_curve=False,
                  ticks=(1, 10),
                  **kwargs):
    """
    Plot a 2D curve.

    Args:
        curve (welly.curve.Curve): Curve object
        ax (ax): A matplotlib axis.
        width (int): The width of the image.
        aspect (int): The aspect ratio (not quantitative at all).
        cmap (str): The colourmap to use.
        plot_curve (bool): Whether to plot the curve as well.
        ticks (tuple): The tick interval on the y-axis.

    Returns:
        ax. If you passed in an ax, otherwise None.
    """
    # Set up the figure.
    if ax is None:
        fig, ax = plt.subplots(figsize=(2, 10))

    # Set up the data.
    cmap = cmap or 'viridis'

    curve_data = curve.as_numpy()
    default = int(curve_data.shape[0] / aspect)
    if curve_data.ndim == 1:
        a = np.expand_dims(curve_data, axis=1)
        a = np.repeat(a, width or default, axis=1)
    elif curve_data.ndim == 2:
        a = curve_data[:, :width] if width < curve_data.shape[1] else curve_data
    elif curve_data.ndim == 3:
        if 2 < curve_data.shape[-1] < 5:
            # Interpret as RGB or RGBA.
            a = utils.normalize(np.copy(curve_data))
            cmap = None  # Actually doesn't matter.
        else:
            # Take first slice.
            a = curve_data[:, :width, 0] if width < curve_data.shape[1] else curve_data[..., 0]
    else:
        raise NotImplementedError("Can only handle up to 3 dimensions.")

    # At this point, a is either a 2D array, or a 2D (rgb) array.
    extent = [np.nanmin(curve_data) or 0, np.nanmax(curve_data) or default, curve.stop, curve.start]
    im = ax.imshow(a, cmap=cmap, extent=extent, aspect='auto')

    if plot_curve:
        paths = ax.fill_betweenx(y=curve.basis,
                                 x1=curve_data,
                                 x2=np.nanmin(curve_data),
                                 facecolor='none',
                                 **kwargs)

        # Make the 'fill' mask and clip the background image with it.
        patch = PathPatch(paths._paths[0], visible=False)
        ax.add_artist(patch)
        im.set_clip_path(patch)
    else:
        # if not plotting a curve, the x-axis is dimensionless
        ax.set_xticks([])

    # Rely on interval order.
    lower, upper = curve.stop, curve.start
    rng = abs(upper - lower)

    ax.set_ylim([lower, upper])

    # Make sure ticks is a tuple.
    try:
        ticks = tuple(ticks)
    except TypeError:
        ticks = (1, ticks)

    # Avoid MAXTICKS error.
    while rng / ticks[0] > 250:
        mi, ma = 10 * ticks[0], ticks[1]
        if ma <= mi:
            ma = 10 * mi
        ticks = (mi, ma)

    # Carry on plotting...
    minorLocator = mpl.ticker.MultipleLocator(ticks[0])
    ax.yaxis.set_minor_locator(minorLocator)

    majorLocator = mpl.ticker.MultipleLocator(ticks[1])
    majorFormatter = mpl.ticker.FormatStrFormatter('%d')
    ax.yaxis.set_major_locator(majorLocator)
    ax.yaxis.set_major_formatter(majorFormatter)

    ax.yaxis.set_ticks_position('left')
    ax.get_yaxis().set_tick_params(which='both', direction='out')
    plt.tight_layout()
    return ax


def plot_curve(curve,
               ax=None,
               legend=None,
               **kwargs):
    """
    Plot a curve.

    Args:
        curve (welly.curve.Curve): Curve object
        ax (ax): A matplotlib axis.
        legend (striplog.legend): A legend. Optional. Should contain kwargs for ax.set().
        kwargs: Arguments for ``ax.plot()``

    Returns:
        ax. If you passed in an ax, otherwise the figure.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(2, 10))

    d = None

    if legend is not None:
        try:
            d = legend.get_decor(curve)
        except:
            pass

    if d is not None:
        kwargs['color'] = d.colour
        kwargs['lw'] = getattr(d, 'lineweight', None) or getattr(d, 'lw', 1)
        kwargs['ls'] = getattr(d, 'linestyle', None) or getattr(d, 'ls', '-')

    ax.plot(curve.df.to_numpy(copy=True), curve.basis, **kwargs)

    if d is not None:
        # Attempt to get axis parameters from decor.
        axkwargs = {}

        xlim = getattr(d, 'xlim', None)
        if xlim is not None:
            axkwargs['xlim'] = list(map(float, xlim.split(',')))

        xticks = getattr(d, 'xticks', None)
        if xticks is not None:
            axkwargs['xticks'] = list(map(float, xticks.split(',')))

        xscale = getattr(d, 'xscale', None)
        if xscale is not None:
            axkwargs['xscale'] = xscale

        ax.set(**axkwargs)

    ax.set_title(curve.df.columns[0])  # no longer needed
    ax.set_xlabel(curve.units)

    if False:  # labeltop of axes?
        ax.xaxis.tick_top()

    if True:  # rotate x-tick labels
        labels = ax.get_xticklabels()
        for label in labels:
            label.set_rotation(90)

    ax.set_ylim([curve.stop, curve.start])
    ax.grid('on', color='k', alpha=0.33, lw=0.33, linestyle='-')

    return ax


def plot_kde_curve(curve,
                   ax=None,
                   amax=None,
                   amin=None,
                   label=None):
    """
    Plot a KDE for the curve. Very nice summary of KDEs:
    https://jakevdp.github.io/blog/2013/12/01/kernel-density-estimation/
    
    Args:
        curve (welly.curve.Curve): Curve object
        ax (axis): Optional matplotlib (MPL) axis to plot into. Returned.
        amax (float): Optional max value to permit.
        amin (float): Optional min value to permit.
        label (string): What to put on the y-axis. Defaults to curve name.

    Returns:
        None, axis, figure: depending on what you ask for. The returned plot is
        a KDE plot for the curve.
    """
    from scipy.stats import gaussian_kde

    if ax is None:
        fig, ax = plt.subplots()

    a = curve.df.dropna().to_numpy()

    # Find values for common axis to exclude outliers.
    if amax is None:
        amax = np.percentile(a, 99)
    if amin is None:
        amin = np.percentile(a, 1)

    x = a[np.abs(a - 0.5 * (amax + amin)) < 0.5 * (amax - amin)]
    x_grid = np.linspace(amin, amax, 100)

    kde = gaussian_kde(x)
    std_a = kde.evaluate(x_grid)

    img = np.array([std_a]) / np.max([std_a])
    extent = [amin, amax, 0, 1]
    ax.imshow(img, aspect='auto', cmap='viridis', extent=extent)
    ax.set_yticklabels([])
    ax.set_ylabel(label or curve.df.columns[0])

    return ax

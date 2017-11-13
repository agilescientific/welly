# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import re
import datetime

import matplotlib.pyplot as plt
import matplotlib as mpl
import lasio
import numpy as np

from . import utils
from .fields import las_fields as LAS_FIELDS
from .curve import Curve
from .header import Header
from .location import Location
from .synthetic import Synthetic
from .canstrat import well_to_card_1
from .canstrat import well_to_card_2
from .canstrat import interval_to_card_7
from .canstrat import write_row

###############################################
# This module is not used directly, but must
# be imported in order to register new scales.
from . import scales  # DO NOT DELETE
###############################################


class WellError(Exception):
    """
    Generic error class.
    """
    pass


class Well(object):
    """
    Well contains everything about the well.
    """
    def __init__(self, params):
        """
        Generic initializer for now.
        """
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

        if getattr(self, 'data', None) is None:
            self.data = {}

        if getattr(self, 'header', None) is None:
            self.header = Header({})

    def __eq__(self, other):
        if (not self.uwi) or (not other.uwi):
            m = "One or both UWIs is blank, cannot determine equality."
            raise WellError(m)
        if self.uwi == other.uwi:
            return True
        return False

    def __nonzero__(self):
        """
        Truthiness.
        """
        if self.header or self.data or self.uwi:
            return True
        return False

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        row1 = '<tr><th style="text-align:center;" '
        row1 += 'colspan="2">{}<br><small>{{}}</small></th></tr>'
        rows = row1.format(getattr(self.header, 'name', ''))
        rows = rows.format(getattr(self.header, 'uwi', ''))
        s = '<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'

        if getattr(self, 'location', None) is not None:
            for k, v in self.location.__dict__.items():
                if k in ['deviation', 'position']:
                    continue
                if k == 'crs':
                    v = v.__repr__()
                rows += s.format(k=k, v=v)

        if getattr(self, 'data', None) is not None:
            v = ', '.join(sorted(list(self.data.keys())))
            rows += s.format(k="data", v=v)

        html = '<table>{}</table>'.format(rows)
        return html

    @property
    def uwi(self):
        """
        Property. Simply a shortcut to the UWI from the header, or the
        empty string if there isn't one.
        """
        return getattr(self.header, 'uwi', None) or ''

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None, data=True, req=None, alias=None, fname=None):
        """
        Constructor. If you already have the lasio object, then this makes a
        well object from it.

        Args:
            l (lasio object): a lasio object.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            data (bool): Whether to load curves or not.
            req (dict): An alias list, giving all required curves. If not
                all of the aliases are present, the well is empty.

        Returns:
            well. The well object.
        """
        # Build a dict of curves.
        curve_params = {}
        for field, (sect, code) in LAS_FIELDS['data'].items():
            curve_params[field] = utils.lasio_get(l,
                                                  sect,
                                                  code,
                                                  remap=remap,
                                                  funcs=funcs)

        # This is annoying, but I need the whole depth array to
        # deal with edge cases, eg non-uniform sampling.

        # Add all required curves together
        if req:
            reqs = utils.flatten_list([v for k, v in alias.items() if k in req])

        # Using lasio's idea of depth in metres:
        curve_params['depth'] = l.depth_m

        # Make the curve dictionary.
        depth_curves = ['DEPT', 'TIME']
        if data and req:
            curves = {c.mnemonic: Curve.from_lasio_curve(c, **curve_params)
                      for c in l.curves
                      if (c.mnemonic[:4] not in depth_curves)
                      and (c.mnemonic in reqs)}
        elif data and not req:
            curves = {c.mnemonic: Curve.from_lasio_curve(c, **curve_params)
                      for c in l.curves
                      if (c.mnemonic[:4] not in depth_curves)}
        elif (not data) and req:
            curves = {c.mnemonic: True
                      for c in l.curves
                      if (c.mnemonic[:4] not in depth_curves)
                      and (c.mnemonic in reqs)}
        else:
            curves = {c.mnemonic: True
                      for c in l.curves
                      if (c.mnemonic[:4] not in depth_curves)}

        if req:
            aliases = utils.flatten_list([c.get_alias(alias)
                                          for m, c
                                          in curves.items()]
                                         )
            if len(set(aliases)) < len(req):
                return cls(params={})

        # Build a dict of the other well data.
        params = {'las': l,
                  'header': Header.from_lasio(l, remap=remap, funcs=funcs),
                  'location': Location.from_lasio(l, remap=remap, funcs=funcs),
                  'data': curves,
                  'fname': fname}

        for field, (sect, code) in LAS_FIELDS['well'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)
        return cls(params)

    @classmethod
    def from_las(cls, fname, remap=None, funcs=None, data=True, req=None, alias=None, encoding=None, printfname=False):
        """
        Constructor. Essentially just wraps ``from_lasio()``, but is more
        convenient for most purposes.

        Args:
            fname (str): The path of the LAS file.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            printfname (bool): prints filename before trying to load it, for 
                debugging

        Returns:
            well. The well object.
        """
        if printfname:
            print(fname)
        l = lasio.read(fname, encoding=encoding)

        # Pass to other constructor.
        return cls.from_lasio(l, remap=remap, funcs=funcs, data=data, req=req, alias=alias, fname=fname)

    def df(self):
        """
        Just use lasio's df().
        """
        return self.las.df()

    def to_lasio(self, basis=None, keys=None):
        """
        Makes a lasio object from the current well.

        Args:
            basis (ndarray): Optional. The basis to export the curves in. If
                you don't specify one, it will survey all the curves with
                ``survey_basis()``.
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.

        Returns:
            lasio. The lasio object.
        """

        # Create an empty lasio object.
        l = lasio.LASFile()
        l.well.DATE = str(datetime.datetime.today())

        # Deal with header.
        for obj, dic in LAS_FIELDS.items():
            if obj == 'data':
                continue
            for attr, (sect, item) in dic.items():
                value = getattr(getattr(self, obj), attr, None)
                try:
                    getattr(l, sect)[item].value = value
                except:
                    h = lasio.HeaderItem(item, "", value, "")
                    getattr(l, sect)[item] = h

        # Clear curves from header portion.
        l.header['Curves'] = []

        # Add a depth basis.
        if basis is None:
            basis = self.survey_basis(keys=keys)
        try:
            l.add_curve('DEPT', basis)
        except:
            raise Exception("Please provide a depth basis.")

        # Add meta from basis.
        setattr(l.well, 'STRT', basis[0])
        setattr(l.well, 'STOP', basis[-1])
        setattr(l.well, 'STEP', basis[1]-basis[0])

        # Add data entities.
        other = ''
        keys = utils.flatten_list(keys) or list(self.data.keys())
        for k in keys:
            d = self.data[k]
            if getattr(d, 'null', None) is not None:
                d[np.isnan(d)] = d.null
            try:
                new_data = np.copy(d.to_basis_like(basis))
            except:
                # Basis shift failed; is probably not a curve
                pass
            try:
                descr = d.description
                l.add_curve(k.upper(), new_data, unit=d.units, descr=descr)
            except:
                try:
                    # Treat as OTHER
                    other += "{}\n".format(k.upper()) + d.to_csv()
                except:
                    pass

        # Write OTHER, if any.
        if other:
            l.other = other

        return l

    def to_las(self, fname, basis=None, keys=None):
        """
        Writes the current well instance as a LAS file. Essentially just wraps
        ``to_lasio()``, but is more convenient for most purposes.

        Args:
            fname (str): The path of the LAS file to create.
            basis (ndarray): Optional. The basis to export the curves in. If
                you don't specify one, it will survey all the curves with
                ``survey_basis()``.
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.

        Returns:
            None. Writes the file as a side-effect.
        """
        with open(fname, 'w') as f:
            self.to_lasio(basis=basis, keys=keys).write(f)

        return

    def add_curves_from_las(self, fname, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            fname (str): The path of the LAS file to read curves from.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
        """
        try:  # To treat as a single file
            self.add_curves_from_lasio(lasio.read(fname),
                                       remap=remap,
                                       funcs=funcs
                                       )
        except:  # It's a list!
            for f in fname:
                self.add_curves_from_lasio(lasio.read(f),
                                           remap=remap,
                                           funcs=funcs
                                           )

        return None

    def add_curves_from_lasio(self, l, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            fname (str): The path of the LAS file to read curves from.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
        """
        params = {}
        for field, (sect, code) in LAS_FIELDS['data'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        curves = {c.mnemonic: Curve.from_lasio_curve(c, **params)
                  for c in l.curves}

        # This will clobber anything with the same key!
        self.data.update(curves)

        return None

    def _plot_depth_track(self, ax, md, kind='MD'):
        """
        Private function. Depth track plotting.

        Args:
            ax (ax): A matplotlib axis.
            md (ndarray): The measured depths of the track.
            kind (str): The kind of track to plot.

        Returns:
            ax.
        """
        if kind == 'MD':
            ax.set_yscale('bounded', vmin=md.min(), vmax=md.max())
            # ax.set_ylim([md.max(), md.min()])
        elif kind == 'TVD':
            tvd = self.location.md2tvd(md)
            ax.set_yscale('piecewise', x=tvd, y=md)
            # ax.set_ylim([tvd.max(), tvd.min()])
        else:
            raise Exception("Kind must be MD or TVD")

        for sp in ax.spines.values():
            sp.set_color('gray')

        if ax.is_first_col():
            pad = -10
            ax.spines['left'].set_color('none')
            ax.yaxis.set_ticks_position('right')
            for label in ax.get_yticklabels():
                label.set_horizontalalignment('right')
        elif ax.is_last_col():
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

    def plot(self,
             legend=None,
             tracks=None,
             track_titles=None,
             alias=None,
             basis=None,
             return_fig=False,
             extents='td',
             **kwargs):
        """
        Plot multiple tracks.

        Args:
            legend (striplog.legend): A legend instance.
            tracks (list): A list of strings and/or lists of strings. The
                tracks you want to plot from ``data``. Optional, but you will
                usually want to give it.
            track_titles (list): Optional. A list of strings and/or lists of
                strings. The names to give the tracks, if you don't want welly
                to guess.
            basis (ndarray): Optional. The basis of the plot, if you don't
                want welly to guess (probably the best idea).
            return_fig (bool): Whether to return the matplotlig figure. Default
                False.
            extents (str): What to use for the y limits:
                'td' — plot 0 to TD.
                'curves' — use a basis that accommodates all the curves.
                'all' — use a basis that accommodates everything.
                (tuple) — give the upper and lower explictly.

        Returns:
            None. The plot is a side-effect.
        """
        # These will be treated differently.
        depth_tracks = ['MD', 'TVD']

        # Set tracks to 'all' if it's None.
        tracks = tracks or list(self.data.keys())
        track_titles = track_titles or tracks

        # Figure out limits
        if basis is None:
            basis = self.survey_basis(keys=tracks)

        if extents == 'curves':
            upper, lower = basis[0], basis[-1]
        elif extents == 'td':
            try:
                upper, lower = 0, self.location.td
            except:
                m = "Could not read self.location.td, try extents='curves'"
                raise WellError(m)
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
        fig = plt.figure(figsize=(2*ntracks, 12), facecolor='w')
        fig.suptitle(self.header.name, size=16, zorder=100,
                     bbox=dict(facecolor='w', alpha=1.0, ec='none'))
        gs = mpl.gridspec.GridSpec(1, ntracks, width_ratios=widths)

        # Plot first axis.
        # kwargs = {}
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.depth_track = False
        track = tracks[0]
        if '.' in track:
            track, kwargs['field'] = track.split('.')
        if track in depth_tracks:
            ax0 = self._plot_depth_track(ax=ax0, md=basis, kind=track)
        else:
            try:  # ...treating as a plottable object.
                ax0 = self.get_curve(track, alias=alias).plot(ax=ax0, legend=legend, **kwargs)
            except AttributeError:  # ...it's not there.
                pass
            except TypeError:  # ...it's a list.
                for t in track:
                    try:
                        ax0 = self.get_curve(t, alias=alias).plot(ax=ax0, legend=legend, **kwargs)
                    except AttributeError:  # ...it's not there.
                        pass
        tx = ax0.get_xticks()
        ax0.set_xticks(tx[1:-1])
        ax0.set_title(track_titles[0])

        # Plot remaining axes.
        for i, track in enumerate(tracks[1:]):
            # kwargs = {}
            ax = fig.add_subplot(gs[0, i+1])
            ax.depth_track = False
            if track in depth_tracks:
                ax = self._plot_depth_track(ax=ax, md=basis, kind=track)
                continue
            if '.' in track:
                track, kwargs['field'] = track.split('.')
            plt.setp(ax.get_yticklabels(), visible=False)
            try:  # ...treating as a plottable object.
                ax = self.get_curve(track, alias=alias).plot(ax=ax, legend=legend, **kwargs)
            except AttributeError:  # ...it's not there.
                continue
            except TypeError:  # ...it's a list.
                for j, t in enumerate(track):
                    if '.' in t:
                        track, kwargs['field'] = track.split('.')
                    try:
                        ax = self.get_curve(t, alias=alias).plot(ax=ax, legend=legend, **kwargs)
                    except AttributeError:
                        continue
                    except KeyError:
                        continue

            tx = ax.get_xticks()
            ax.set_xticks(tx[1:-1])
            ax.set_title(track_titles[i+1])

        # Set sharing.
        axes = fig.get_axes()
        utils.sharey(axes)
        axes[0].set_ylim([lower, upper])

        # Adjust the grid.
        gs.update(wspace=0)

        # Adjust spines and ticks for non-depth tracks.
        for ax in axes:
            if ax.depth_track:
                pass
            if not ax.depth_track:
                ax.set(yticks=[])
                ax.autoscale(False)
                ax.yaxis.set_ticks_position('none')
                ax.spines['top'].set_visible(True)
                ax.spines['bottom'].set_visible(True)
                for sp in ax.spines.values():
                    sp.set_color('gray')

        if return_fig:
            return fig
        else:
            return None

    def survey_basis(self, keys=None, alias=None, step=None):
        """
        Look at the basis of all the curves in the ``well.data`` and return a
        basis with the minimum start, maximum depth, and minimum step.

        Args:
            keys (list): List of strings: the keys of the data items to
                survey, if not all of them.

        Returns:
            ndarray. The 'most complete common basis'.
        """
        keys = utils.flatten_list(keys)
        starts, stops, steps = [], [], []
        for k in self.data:
            d = self.get_curve(k, alias=alias)
            if (keys is not None) and (d is None):
                continue
            try:
                starts.append(d.basis[0])
                stops.append(d.basis[-1])
                steps.append(d.basis[1] - d.basis[0])
            except Exception as e:
                pass
        if starts and stops and steps:
            step = step or min(steps)
            return np.arange(min(starts), max(stops)+1e-9, step)
        else:
            return None

    def unify_basis(self, keys=None):
        """
        Give everything, or everything in the list of keys, the same basis.
        Args:
            keys (list): List of strings: the keys of the data items to
                unify, if not all of them.

        Returns:
            None. Works in place.
        """
        basis = self.survey_basis(keys=keys)
        if basis is None:
            raise WellError("Could not retrieve common basis.")

        for k in self.data:
            if (keys is not None) and (k not in keys):
                continue
            try:  # To treat as a curve.
                self.data[k] = self.data[k].to_basis(basis)
            except:  # It's probably a striplog.
                continue

        return

    def get_mnemonics_from_regex(self, pattern):
        """
        Should probably integrate getting curves with regex, vs getting with
        aliases, even though mixing them is probably confusing. For now I can't
        think of another use case for these wildcards, so I'll just implement
        for the curve table and we can worry about a nice solution later if we
        ever come back to it.
        """
        regex = re.compile(pattern)
        keys = self.data.keys()
        return [m.group(0) for k in keys for m in [regex.search(k)] if m]

    def get_mnemonic(self, mnemonic, alias=None):
        """
        Instead of picking curves by name directly from the data dict, you
        can pick them up with this method, which takes account of the alias
        dict you pass it. If you do not pass an alias dict, then you get the
        curve you asked for, if it exists, or None. NB Wells do not have alias
        dicts, but Projects do.

        Args:
            mnemonic (str): the name of the curve you want.
            alias (dict): an alias dictionary, like welly.

        Returns:
            Curve.
        """
        alias = alias or {}
        aliases = alias.get(mnemonic, [mnemonic])
        for a in aliases:
            if a in self.data:
                return a
        return None

    def get_curve(self, mnemonic, alias=None):
        """
        Wraps get_mnemonic.

        Instead of picking curves by name directly from the data dict, you
        can pick them up with this method, which takes account of the alias
        dict you pass it. If you do not pass an alias dict, then you get the
        curve you asked for, if it exists, or None. NB Wells do not have alias
        dicts, but Projects do.

        Args:
            mnemonic (str): the name of the curve you want.
            alias (dict): an alias dictionary, like welly.

        Returns:
            Curve.
        """
        return self.data.get(self.get_mnemonic(mnemonic, alias=alias), None)

    def count_curves(self, keys=None, alias=None):
        """
        Counts the number of curves in the well that will be selected with the
        given key list and the given alias dict. Used by Project's curve table.
        """
        keys = keys or list(self.data.keys())
        return len(list(filter(None, [self.get_mnemonic(k, alias=alias) for k in keys])))

    def is_complete(self, keys=None, alias=None):
        """
        Returns False if the well does not have one or more of the keys in its
        data dictionary. Used by project.data_to_matrix().
        """
        return any(k not in self.data.keys() for k in keys)

    def alias_has_multiple(self, mnemonic, alias):
        return 1 < len([a for a in alias[mnemonic] if a in self.data])

    def make_synthetic(self,
                       srd=0,
                       v_repl_seismic=2000,
                       v_repl_log=2000,
                       f=50,
                       dt=0.001):
        """
        Early hack. Use with extreme caution.

        Hands-free. There'll be a more granualr version in synthetic.py.

        Assumes DT is in µs/m and RHOB is kg/m3.

        There is no handling yet for TVD.

        The datum handling is probably sketchy.

        TODO:
            A lot.
        """
        kb = getattr(self.location, 'kb', None) or 0
        data0 = self.data['DT'].start
        log_start_time = ((srd - kb) / v_repl_seismic) + (data0 / v_repl_log)

        # Basic log values.
        dt_log = self.data['DT'].despike()  # assume µs/m
        rho_log = self.data['RHOB'].despike()  # assume kg/m3
        if not np.allclose(dt_log.basis, rho_log.basis):
            rho_log = rho_log.to_basis_like(dt_log)
        Z = (1e6 / dt_log) * rho_log

        # Two-way-time.
        scaled_dt = dt_log.step * np.nan_to_num(dt_log) / 1e6
        twt = 2 * np.cumsum(scaled_dt)
        t = twt + log_start_time

        # Move to time.
        t_max = t[-1] + 10*dt
        t_reg = np.arange(0, t_max+1e-9, dt)
        Z_t = np.interp(x=t_reg, xp=t, fp=Z)

        # Make RC series.
        rc_t = (Z_t[1:] - Z_t[:-1]) / (Z_t[1:] + Z_t[:-1])
        rc_t = np.nan_to_num(rc_t)

        # Convolve.
        _, ricker = utils.ricker(f=f, length=0.128, dt=dt)
        synth = np.convolve(ricker, rc_t, mode='same')

        params = {'dt': dt,
                  'z start': dt_log.start,
                  'z stop': dt_log.stop
                  }

        self.data['Synthetic'] = Synthetic(synth, basis=t_reg, params=params)

        return None

    def qc_curve_group(self, tests, alias=None):
        """
        Run tests on a cohort of curves.
        """
        keys = [k for k, v in self.data.items() if isinstance(v, Curve)]
        if not keys:
            return {}

        all_tests = tests.get('all', tests.get('All', tests.get('ALL', [])))
        data = {test.__name__: test(self, keys, alias) for test in all_tests}

        results = {}
        for i, key in enumerate(keys):
            this = {}
            for test, result in data.items():
                this[test] = result[i]
            results[key] = this
        return results

    def qc_data(self, tests, alias=None):
        """
        Run a series of tests against the data and return the corresponding
        results.

        Args:
            tests (list): a list of functions.

        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # We'll get a result for each curve here.
        r = {m: c.quality(tests, alias) for m, c in self.data.items()}

        s = self.qc_curve_group(tests, alias=alias)

        for m, results in r.items():
            if m in s:
                results.update(s[m])

        return r

    def qc_table_html(self, tests, alias=None):
        """
        Makes a nice table out of ``qc_data()``
        """
        data = self.qc_data(tests, alias=alias)
        all_tests = [list(d.keys()) for d in data.values()]
        tests = list(set(utils.flatten_list(all_tests)))

        # Header row.
        r = '</th><th>'.join(['Curve', 'Passed', 'Score'] + tests)
        rows = '<tr><th>{}</th></tr>'.format(r)

        styles = {
            True: "#CCEECC",
            False: "#FFCCCC",
        }

        # Quality results.
        for curve, results in data.items():

            if results:
                norm_score = sum(results.values()) / len(results)
            else:
                norm_score = -1

            rows += '<tr><th>{}</th>'.format(curve)
            rows += '<td>{} / {}</td>'.format(sum(results.values()), len(results))
            rows += '<td>{:.3f}</td>'.format(norm_score)

            for test in tests:
                result = results.get(test, '')
                style = styles.get(result, "#EEEEEE")
                rows += '<td style="background-color:{};">'.format(style)
                rows += '{}</td>'.format(result)
            rows += '</tr>'

        html = '<table>{}</table>'.format(rows)
        return html

    def to_canstrat(self, key, log, lith_field, filename=None, as_text=False):
        """
        Make a Canstrat DAT (aka ASCII) file.

        TODO:
            The data part should probably belong to striplog, and only the
            header should be written by the well.

        Args:
           filename (str)
           key (str)
           log (str): the log name, should be 6 characters.
           lith_field (str) the name of the lithology field in the striplog's
               Primary component. Must match the Canstrat definitions.
           filename (str)
           as_text (bool): if you don't want to write a file.
        """
        if (filename is None):
            if (not as_text):
                m = "You must provide a filename or set as_text to True."
                raise WellError(m)

        strip = self.data[key]
        strip = strip.fill()  # Default is to fill with 'null' intervals.

        record = {1: [well_to_card_1(self)],
                  2: [well_to_card_2(self, key)],
                  8: [],
                  7: [interval_to_card_7(iv, lith_field) for iv in strip]
                  }

        result = ''
        for c in [1, 2, 8, 7]:
            for d in record[c]:
                result += write_row(d, card=c, log=log)

        if as_text:
            return result
        else:
            with open(filename, 'w') as f:
                f.write(result)
            return None

    def data_as_matrix(self, keys=None,
                       return_basis=False,
                       basis=None,
                       start=None,
                       stop=None,
                       step=None,
                       window_length=None,
                       window_step=1,
                       alias=None):
        """
        Provide a feature matrix, given a list of data items.

        I think this will probably fail if there are striplogs in the data
        dictionary for this well.



        TODO:
            Deal with striplogs and other data, if present.

        Args:
            keys (list): List of the logs to export from the data dictionary.
            return_basis (bool): Whether or not to return the basis that was
                used.
            basis (ndarray): The basis to use. Default is to survey all curves
                to find a common basis.
            start (float): Optionally override the start of whatever basis
                you find or (more likely) is surveyed.
            stop (float): Optionally override the stop of whatever basis
                you find or (more likely) is surveyed.
            window (int): The number of samples to return around each sample.
            step (float): Override the step in the basis from survey_basis.

        """
        if keys is None:
            keys = list(self.data.keys())
        else:
            # Only look at the alias list if keys were passed.
            if alias is not None:
                _keys = []
                for k in keys:
                    if k in alias:
                        added = False
                        for a in alias[k]:
                            if a in self.data:
                                _keys.append(a)
                                added = True
                                break
                        if not added:
                            _keys.append(k)
                    else:
                        _keys.append(k)
                # print("You asked for {}".format(keys))
                # print("You are getting {}".format(_keys))
                keys = _keys

        if basis is None:
            basis = self.survey_basis(keys=keys, step=step)

        # Get the data, or None is curve is missing.
        data = [self.data.get(k) for k in keys]

        # Now cast to the correct basis, and replace any missing curves with
        # an empty Curve. The sklearn imputer will deal with it. We will change
        # the elements in place.
        for i, d in enumerate(data):
            if d is not None:
                data[i] = d.to_basis(basis=basis)
                # Allow user to override the start and stop from the survey.
                if (start is not None) or (stop is not None):
                    data[i] = data[i].to_basis(start=start, stop=stop, step=step)
                    basis = data[i].basis
            else:
                # Empty_like gives unpredictable results
                data[i] = Curve(np.full(basis.shape, np.nan), basis=basis)

        if window_length is not None:
            d_new = []
            for d in data:
                r = d._rolling_window(window_length,
                                      func1d=utils.null,
                                      step=window_step,
                                      return_rolled=False,
                                      )
                d_new.append(r.T)
            data = d_new

        if return_basis:
            return np.vstack(data).T, basis
        else:
            return np.vstack(data).T

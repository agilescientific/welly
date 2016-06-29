# !/usr/bin/env python
"""
Makes scorecard for a well.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as PathEffects

# from .well import Well

track_titles = ['MD',
                'Lithology',
                'Resistivity',
                'Porosity',
                'Density',
                'Sonic',
                'Canstrat']

curve_layout = {'C1': 0, 'CALS': 0, 'CAX': 0, 'CAY': 0, 'CALI': 0,
                'GR': 1, 'GAM': 1,
                'PEF': 1, 'SP': 1,
                'ILD': 2, 'ILM': 2, 'SFL': 2, 'CILD': 2, 'NOR': 2, 'MFR': 2,
                'LL8': 2, 'LLD': 2, 'LLS': 2, 'INV': 2,
                'NPSS': 3, 'PDS': 3, 'NPLS': 3, 'DPSS': 3, 'DPLS': 3,
                'POS': 3, 'POL': 3,
                'RHOB': 4, 'DEN': 4, 'DRHO': 4, 'DC': 4, 'DTLN': 4,
                'DT': 5, 'DT4P': 5, 'AC': 5, 'ACL': 5}

colours = OrderedDict([('green', ['MV', 'B/E', 'GAPI', 'NAPI', 'API', 'MM']),
                       ('magenta', ['OHM/M', 'MMHO/M', 'OHM.M', 'OHMM']),
                       ('red', ['V/V', '%', 'PU', 'M3/M3', 'DEC']),
                       ('blue', ['G/CM3', 'K/M3', 'G/C3', 'KGM3', 'KG/M3']),
                       ('navy', ['US/M', 'US/F', 'US/FT', 'USEC/M']),
                       ('grey', [])])


class Inventory(Well):
    """
    Creates a scorecard representation of a well.
    """


    def __init__(self, well):
        """
        Generic initializer for now.
        """
        self.data = well.data
        self.location = well.location
        self.header = well.header
        self.width  = 8  # width of scorecard plot in inches
        self.vscale = 250  # meters per inch (vertical scale)
        self.striplog = well.data['Canstrat']
        self.topsdata = well.data['tops']
        if not well.location.td:
            self.location.td = well.survey_basis()[-1]


    def scorecard_fig(self):
        """
        Makes a well scorecard figure from contents of a well object
        param: vscale: vertical scale in metres per inch.
        """
        fig = plt.figure(figsize=(8, 6))
        gs = gridspec.GridSpec(1, 6, width_ratios=[3, 3, 3, 3, 3, 1])
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        ax3 = plt.subplot(gs[2])
        ax4 = plt.subplot(gs[3])
        ax5 = plt.subplot(gs[4])
        ax6 = plt.subplot(gs[5])
        axarr = [ax1, ax2, ax3, ax4, ax5, ax6]
        return fig, axarr


    def plot_bars(self, axarr, fs=8, start=0, buff=0.2):
        """
        Plots various bars in tracks.
        """
        trackplace = np.zeros(len(axarr))
        basis = self.data['DEPT'] 
        for curve in self.data.keys():
            if type(self.data[curve]) == type(basis):
                if curve != 'DEPT' or 'DEPTH':
                    top, base, height = self.get_bar_range(self.data[curve])
                    name, units, descr = self.get_curve_text(self.data[curve])

                    # This is a little convoluted because the dictionary is backwards.
                    # Alternative would be to reverse it, and just use the set of colours
                    # for the colour index lookup.
                    _colour = [k if (units.upper() in v) else None for k, v in colours.items()]
                    colour = (list(filter(None, _colour)) or ['grey'])[0]
                    p = list(colours.keys()).index(colour)

                    ax = axarr[p]
                    # Plot the bar
                    for t, b, h in zip(top, base, height):
                        ax.bar(start + trackplace[p] + buff, h, bottom=self.data[curve].basis[t],
                               width=0.8, alpha=0.2, color=colour)
                        # Plot the name in the middle
                        ax.text(start + trackplace[p] + 0.5 + buff, 0 + 350, name,
                                fontsize=fs, ha='center', va='top', rotation='vertical')
                        # Plot curve units
                        ax.text(start + trackplace[p] + 0.5 + buff, 0 + 50, units,
                                fontsize=fs, ha='center', va='top', rotation='vertical')
                    ax.set_ylim([self.location.td, 0])
                    trackplace[p] += 1

        [ax.set_xlim(-1, max(trackplace)+1) for ax in axarr]
        [ax.set_yticks([]) for ax in axarr[1:]]
        [ax.set_xticks([]) for ax in axarr]
        return axarr

    def get_bar_range(self, curve):
        '''
        Returns the depth of the bottom of the log (and the height) for bar chart.
        '''
        tops = []    # top of log
        bots = []    # bottom of log
        # find index of first real value of curve
        index = np.where(np.isfinite(np.array(curve)))[0]
        tops.append(index[0])
        # find bottom of log or missing points
        for i in np.arange(index.size - 1):
            if (index[i + 1] - index[i]) > 1:
                bots.append(index[i])
                # print ('null value here: ', i, ' index', index[i])
                tops.append(index[i + 1])
        bots.append(index[-1])
        top = np.asarray(tops)
        base = np.asarray(bots)
        height = curve.basis[base] - curve.basis[top]
        return top, base, height

    def get_curve_text(self, curve):
        name = curve.mnemonic
        units = curve.units
        descr = curve.description
        return name, units, descr

    def put_track_names(self, axarr, fs=10):
        """
        Puts label of track type in each track.
        """
        for ax, text in zip(axarr[:-1], track_titles[1:-1]):
            ax.text(x=0.5, y=0.0, s=text, fontsize=14,
                    ha='center', va='bottom', transform=ax.transAxes)
        return

    def plot_striplog(self, axarr, striplog, legend):
        """
        Plot stiplog (if the well has one).
        """
        if striplog is not None:
            axarr[-1] = striplog.plot(ax=axarr[-1], aspect=0.2,
                                      legend=legend, match_only=['lithology'])
            axarr[-1].set_title('Canstrat \n Lithology')
            axarr[-1].set_ylim([self.location.td, 0])
            axarr[-1].set_yticklabels([])
            axarr[-1].spines['right'].set_visible(True)
            axarr[-1].spines['top'].set_visible(True)
            axarr[-1].spines['bottom'].set_visible(True)
        return

    def put_tops(self, axarr, topsdata):
        """
        Put tops across all tracks.
        """
        if topsdata is not None:
            for i, ax in enumerate(axarr):
                ax.set_ylim([self.location.td, 0])
                ax.set_xticks([])
                if i > 0:
                    ax.set_yticks([])

                for pick in topsdata:
                    name = pick.data['formation']
                    depth = pick.top.middle
                    ax.axhline(depth, lw=2, color='k', xmax=1.05,
                               path_effects=[PathEffects.SimpleLineShadow(),
                                             PathEffects.Normal()])
                    if i == len(axarr)-1:
                        ax.text(x=ax.get_xlim()[-1]*1.0*1.1, y=depth, s=name,
                                ha='left', va='center')
        return


    def put_side_text(self, axarr):
        # Label kb elevation.
        ax = axarr[-1]
        if self.location.kb is not None:
            ax.text(x=1.4, y=1.0, s='KB elev.:'+str(self.location.kb)+' m',
                    fontsize=8, ha='left', va='top', transform=ax.transAxes)
        # Label td elevation (measured depth)
        if self.location.td is not None:
            ax.text(x=1.4, y=0.0, s='TD:'+str(round(self.location.td))+' m',
                    fontsize=8, ha='left', va='bottom', transform=ax.transAxes)
        return


    def put_header_text(self, fig):
        fig.text(x=0.05, y=0.925, s=self.header.name, fontsize=14)
        fig.text(x=0.05, y=0.910, s='UWI: '+ self.header.uwi, fontsize=12)
        fig.subplots_adjust(wspace=0, hspace=0)
        return fig


    def adjust_fig_dims(self, fig):
        fig.set_figheight(self.location.td/self.vscale)
        fig.set_figwidth(self.width)
        return fig


    def scorecard(self, strip_name, strip_legend, tops_name='none'):
        fig, axarr = self.scorecard_fig()
        axarr = self.plot_bars(axarr)
        self.put_track_names(axarr)
        self.plot_striplog(axarr, self.data[strip_name], strip_legend)
        self.put_tops(axarr, self.data[tops_name])
        self.put_side_text(axarr)
        self.put_header_text(fig)
        self.adjust_fig_dims(fig)
        return fig
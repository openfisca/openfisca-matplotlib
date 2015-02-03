# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import numpy as np

from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrow, Rectangle
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


from openfisca_core.rates import average_rate, marginal_rate
from openfisca_matplotlib.utils import OutNode


def draw_waterfall(simulation, axes = None, decomposition_json = None, period = None, visible = None):
    if axes is None:
        fig = plt.figure()
        axes = fig.gca()
    currency = simulation.tax_benefit_system.CURRENCY
    data = OutNode.init_from_decomposition_json(
        simulation = simulation,
        decomposition_json = decomposition_json,
        period = period,
        )
    data.setLeavesVisible()
    if visible is not None:
        for code in visible:
            data[code].visible = 1
    axes.clear()
    draw_waterfall_from_node_data(data, axes, currency)


def draw_bareme(simulation, axes = None, x_axis = None, reference_simulation = None, decomposition_json = None,
                visible_lines = None, hide_all = False, legend = True, legend_position = None, period = None):
    if axes is None:
        fig = plt.figure()
        axes = fig.gca()
    currency = simulation.tax_benefit_system.CURRENCY
    if legend_position is None:
        legend_position = 2
    is_reform = False
    if simulation is not None and reference_simulation is not None:
        data = OutNode.init_from_decomposition_json(
            simulation = simulation,
            decomposition_json = decomposition_json,
            period = period,
            )
        reference_data = OutNode.init_from_decomposition_json(
            simulation = reference_simulation,
            decomposition_json = decomposition_json,
            period = period,
            )
        is_reform = True
        data.difference(reference_data)
    else:
        data = OutNode.init_from_decomposition_json(
            simulation = simulation,
            decomposition_json = decomposition_json,
            period = period,
            )
        reference_data = None
    data.setLeavesVisible()
    if visible_lines is not None:
        for code in visible_lines:
            data[code].visible = 1
            data[code].typevar = 2


    data[x_axis].setHidden(changeParent = True)
    if is_reform and hide_all is True:
        data.hideAll()
    axes.clear()

    draw_bareme_from_node_data(
        data,
        axes,
        x_axis,
        reform = is_reform,
        legend = legend,
        reference_data = reference_data,
        currency = currency,
        legend_position = legend_position,
        )


def draw_rates(simulation, axes = None, x_axis = None, y_axis = None, reference_simulation = None, legend = True,
               period = None):
    if axes is None:
        fig = plt.figure()
        axes = fig.gca()
    assert x_axis is not None
    assert y_axis is not None
    varying = simulation.calculate(x_axis, period = period)
    target = simulation.calculate(y_axis, period = period)
    avg_rate = average_rate(target, varying)
    marg_rate = marginal_rate(target, varying)
    axes.hold(True)
    axes.set_xlim(np.amin(varying), np.amax(varying))
    axes.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    axes.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    axes.plot(varying, 100 * avg_rate, label = u"Taux moyen d'imposition", linewidth = 2)
    axes.plot(varying[1:], 100 * marg_rate, label = u"Taux marginal d'imposition", linewidth = 2)
    axes.set_ylim(0, 100)

    axes.yaxis.set_major_formatter(FuncFormatter(percent_formatter))
    if legend:
        create_legend(axes)


def percent_formatter(x, pos = 0):
    return '%1.0f%%' % (x)


def create_legend(ax, position = 2):
    '''
    Creates legend
    '''

    p = []
    l = []
    for collec in ax.collections:
        if collec._visible:
            p.insert(0, Rectangle((0, 0), 1, 1, fc = collec._facecolors[0], linewidth = 0.5, edgecolor = 'black'))
            l.insert(0, collec._label)
    for line in ax.lines:
        if line._visible and (line._label != 'x_axis'):
            p.insert(0, Line2D([0, 1], [.5, .5], color = line._color))
            l.insert(0, line._label)
    ax.legend(p, l, loc = position, prop = {'size': 'medium'})


def draw_waterfall_from_node_data(data, ax, currency = None):

    ax.figure.subplots_adjust(bottom = 0.15, right = 0.95, top = 0.95, left = 0.1)
    barwidth = 0.8
    number = [0]
    patches = []
    codes = []
    shortnames = []

    def drawNode(node, prv):
        prev = prv + 0
        val = node.vals[0]
        bot = prev
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals[0]
        if (val != 0) and node.visible:
            r, g, b = node.color
            arrow = FancyArrow(
                number[0] + barwidth / 2, bot, 0, val,
                width = barwidth,
                fc = (r / 255, g / 255, b / 255), linewidth = 0.5, edgecolor = 'black',
                label = node.desc, picker = True, length_includes_head = True,
                head_width = barwidth,
                head_length = abs(val / 15),
                )
            arrow.top = bot + max(0, val)
            arrow.absci = number[0] + 0
#            a = Rectangle((number[0], bot), barwidth, val, fc = node.color, linewidth = 0.5, edgecolor = 'black', label = node.desc, picker = True)
            arrow.value = round(val)
            patches.append(arrow)
            codes.append(node.code)
            shortnames.append(node.shortname)
            number[0] += 1

    prv = 0
    drawNode(data, prv)
    for patch in patches:
        ax.add_patch(patch)

    n = len(patches)
    abscisses = np.arange(n)
    xlim = (- barwidth * 0.5, n - 1 + barwidth * 1.5)
    ax.hold(True)
    ax.plot(xlim, [0, 0], color = 'black')
    ax.set_xticklabels(shortnames, rotation = '45')
    ax.set_xticks(abscisses + barwidth / 2)
    ax.set_xlim((-barwidth / 2, n - 1 + barwidth * 1.5))
    ticks = ax.get_xticklines()
    for tick in ticks:
        tick.set_visible(False)

    for rect in patches:
        x = rect.absci
        y = rect.top
        val = u'{} {}'.format(int(rect.value), currency)
        width = barwidth
        if rect.value >= 0:
            col = 'black'
        else:
            col = 'red'
        ax.text(x + width / 2, y + 1, val, horizontalalignment = 'center',
                verticalalignment = 'bottom', color= col, weight = 'bold')
    m, M = ax.get_ylim()
    ax.set_ylim((m, 1.05 * M))


def draw_bareme_from_node_data(
        data,
        axes,
        x_axis,
        reference_data = None,
        reform = False,
        legend = True,
        currency = None,
        legend_position = 2
        ):
    '''
    Draws bareme
    '''
    if reference_data is None:
        reference_data = data
    axes.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
    if reform:
        prefix = 'Variation '
    else:
        prefix = ''
    axes.hold(True)
    x_axis_data = reference_data[x_axis]
    n_points = len(x_axis_data.vals)
    xlabel = x_axis_data.desc
    axes.set_xlabel(xlabel)
    axes.set_ylabel(prefix + u"{} ({} par an)".format(data.code, currency))
    axes.set_xlim(np.amin(x_axis_data.vals), np.amax(x_axis_data.vals))
    if not reform:
        axes.set_ylim(np.amin(x_axis_data.vals), np.amax(x_axis_data.vals))
    axes.plot(x_axis_data.vals, np.zeros(n_points), color = 'black', label = 'x_axis')

    def drawNode(node, prv):
        prev = prv + 0
        if np.any(node.vals != 0) and node.visible:
            r, g, b = node.color
            col = (r / 255, g / 255, b / 255)
            if node.typevar == 2:
                a = axes.plot(
                    x_axis_data.vals,
                    node.vals,
                    color = col,
                    linewidth = 2,
                    label = prefix + node.desc,
                    )
            else:
                a = axes.fill_between(
                    x_axis_data.vals,
                    prev + node.vals,
                    prev,
                    color = col,
                    linewidth = 0.2,
                    edgecolor = 'black',
                    picker = True,
                    )
                a.set_label(prefix + node.desc)
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals

    prv = np.zeros(n_points)
    drawNode(data, prv)
    if legend:
        create_legend(axes, position = legend_position)


def draw_bareme_comparing_households_from_node_data(
        data, ax, x_axis, dataDefault = None, legend = True, currency = "", position = 2
        ):
    '''
    Draws bareme
    '''
    if dataDefault is None:
        raise Exception('draw_bareme_comparing_households_from_node_data: dataDefault must be defined')

    ax.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
    prefix = 'Variation '
    ax.hold(True)
    xdata = dataDefault[x_axis]
    NMEN = len(xdata.vals)
    xlabel = xdata.desc
    ax.set_xlabel(xlabel)
    ax.set_ylabel(prefix + u"Revenu disponible (" + currency + " par an)")
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    ax.plot(xdata.vals, np.zeros(NMEN), color = 'black', label = 'x_axis')
    node_list = ['af', 'cf', 'ars', 'rsa', 'aefa', 'psa', 'logt', 'irpp', 'ppe', 'revdisp']
    prv = np.zeros(NMEN)

    for nod in node_list:
        node = data[nod]
        prev = prv + 0
        r, g, b = node.color
        col = (r / 255, g / 255, b / 255)
        if node.typevar == 2:
            a = ax.plot(
                xdata.vals,
                node.vals,
                color = col,
                linewidth = 2,
                label = prefix + node.desc,
                )
        else:
            a = ax.fill_between(
                xdata.vals,
                prev + node.vals,
                prev,
                color = col,
                linewidth = 0.2,
                edgecolor = 'black',
                picker = True
                )
            a.set_label(prefix + node.desc)
        prv += node.vals

    if legend:
        create_legend(ax, position = position)


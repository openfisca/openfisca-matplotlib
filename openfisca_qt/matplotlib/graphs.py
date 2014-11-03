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


from openfisca_qt.plugins.utils import OutNode
from openfisca_qt.plugins.scenario.graph import drawBareme, drawWaterfall


def draw_waterfall(simulation, axes, visible = None):
    currency = simulation.tax_benefit_system.CURRENCY
    data = OutNode.init_from_decomposition_json(
        simulation = simulation,
        decomposiiton_json = None,
        )
    data.setLeavesVisible()
    if visible is not None:
        for code in visible:
            data[code].visible = 1
    axes.clear()
    drawWaterfall(data, axes, currency)


def draw_bareme(simulation, axes, x_axis, reference_simulation = None, visible_lines = None, hide_all = False):
    currency = simulation.tax_benefit_system.CURRENCY
    is_reform = False
    if simulation is not None and reference_simulation is not None:
        data = OutNode.init_from_decomposition_json(
            simulation = simulation,
            decomposiiton_json = None,
            )
        reference_data = OutNode.init_from_decomposition_json(
            simulation = reference_simulation,
            decomposiiton_json = None,
            )
        is_reform = True
        data.difference(reference_data)
    else:
        data = OutNode.init_from_decomposition_json(
            simulation = simulation,
            decomposiiton_json = None,
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
    drawBareme(
        data,
        axes,
        x_axis,
        reform = is_reform,
        legend = True,
        reference_data = reference_data,
        currency = currency
        )


def draw_rates(simulation, axes, x_axis = None, y_axis = None, reference_simulation = None, legend = True):
    assert x_axis is not None
    assert y_axis is not None
    from openfisca_core.rates import average_rate, marginal_rate
    varying = simulation.calculate(x_axis)
    target = simulation.calculate(y_axis)
    avg_rate = average_rate(target, varying)
    marg_rate = marginal_rate(target, varying)
    print avg_rate
    axes.hold(True)
    import numpy as np
    axes.set_xlim(np.amin(varying), np.amax(varying))
    axes.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    axes.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    axes.plot(varying, 100*avg_rate, label = u"Taux moyen d'imposition", linewidth = 2)
    axes.plot(varying[1:], 100*marg_rate, label = u"Taux marginal d'imposition", linewidth = 2)
    axes.set_ylim(0, 100)

    from matplotlib.ticker import FuncFormatter
    axes.yaxis.set_major_formatter(FuncFormatter(percentFormatter))
    if legend:
        createLegend(axes)


def percentFormatter(x, pos=0):
    return '%1.0f%%' % (x)


def createLegend(ax, position = 2):
    '''
    Creates legend
    '''
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle

    p = []
    l = []
    for collec in ax.collections:
        if collec._visible:
            p.insert(0, Rectangle((0, 0), 1, 1, fc = collec._facecolors[0], linewidth = 0.5, edgecolor = 'black' ))
            l.insert(0, collec._label)
    for line in ax.lines:
        if line._visible and (line._label != 'x_axis'):
            p.insert(0, Line2D([0,1],[.5,.5],color = line._color))
            l.insert(0, line._label)
    ax.legend(p,l, loc= position, prop = {'size':'medium'})
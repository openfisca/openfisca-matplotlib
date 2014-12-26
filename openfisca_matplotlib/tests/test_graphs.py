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


import datetime
import sys

from PyQt4.Qt import QMainWindow, QApplication

from openfisca_core import periods, reforms
import openfisca_france
from openfisca_matplotlib.widgets.matplotlibwidget import MatplotlibWidget
from openfisca_matplotlib import graphs

TaxBenefitSystem = openfisca_france.init_country()
tax_benefit_system = TaxBenefitSystem()
print tax_benefit_system.DECOMP_DIR


class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)


def waterfall():
    simulation, _ = create_simulation()

    app = QApplication(sys.argv)
    win = ApplicationWindow()

    axes = win.mplwidget.axes
    title = "Mon titre"
    axes.set_title(title)
    simulation.calculate('revdisp')
    graphs.draw_waterfall(
        simulation = simulation,
        axes = axes,
        )
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def bareme():
    reform_simulation, reference_simulation = create_simulation(bareme = True)

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes
    reference_simulation.calculate('revdisp')
    reform_simulation.calculate('revdisp')
    graphs.draw_bareme(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'sal',
        visible_lines = ['revdisp'])
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def rates():
    reform_simulation, reference_simulation = create_simulation(bareme = True)
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes
    graphs.draw_rates(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'sali',
        y_axis = 'revdisp',
        reference_simulation = reference_simulation,
        )
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def bareme_compare_household():
    simulation_1p, simulation_2p = create_simulation2()

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes

    simulation_1p.calculate('revdisp')
    simulation_2p.calculate('revdisp')
    graphs.draw_bareme(
        simulation = simulation_2p,
        axes = axes,
        x_axis = 'sal',
        reference_simulation = simulation_1p,
        visible_lines = ['revdisp'],
        )
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def create_simulation2(year = 2014, bareme = False):
    parent1 = dict(
        birth = datetime.date(year - 40, 1, 1),
        sali = 4000 if bareme is False else None,
        )
    parent2 = dict(
        birth = datetime.date(year - 40, 1, 1),
        sali = 1000,
        )
    # Adding a husband/wife on the same tax sheet (foyer)
    menage = dict(
        loyer = 1000,
        so = 4,
        )
    axes = [
        dict(
            count = 100,
            name = 'sali',
            max = 30000,
            min = 0,
            ),
        ]
    scenario_1p = tax_benefit_system.new_scenario().init_single_entity(
        axes = axes if bareme else None,
        menage = menage,
        parent1 = parent1,
        period = periods.period('year', year),
        )
    simulation_1p = scenario_1p.new_simulation(debug = True)

    scenario_2p = tax_benefit_system.new_scenario().init_single_entity(
        axes = axes if bareme else None,
        menage = menage,
        parent1 = parent1,
        parent2 = parent2,
        period = periods.period('year', year),
        )
    simulation_2p = scenario_2p.new_simulation(debug = True)

    return simulation_1p, simulation_2p


def create_simulation(year = 2014, bareme = False):

    simulation_period = periods.period('year', year)
    reference_legislation_json = tax_benefit_system.legislation_json
    reform_legislation_json = reforms.update_legislation(
        legislation_json = reference_legislation_json,
        path = ('children', 'ir', 'children', 'bareme', 'slices', 0, 'rate'),
        period = simulation_period,
        value = 1,
        )

    reform = reforms.Reform(
        name = u'IR_100_tranche_1',
        label = u"Imposition à 100% dès le premier euro et jusqu'à la fin de la 1ère tranche",
        legislation_json = reform_legislation_json,
        reference = tax_benefit_system
        )
    parent1 = dict(
        birth = datetime.date(year - 40, 1, 1),
        sali = 10000 if bareme is False else None,
        )
#    parent2 = dict(
#        birth = datetime.date(year - 40, 1, 1),
#        sali = 0,
#        )
    # Adding a husband/wife on the same tax sheet (foyer)
    menage = dict(
        loyer = 1000,
        so = 4,
        )
    axes = [
        dict(
            count = 200,
            name = 'sali',
            max = 300000,
            min = 0,
            ),
        ]
    scenario = reform.new_scenario().init_single_entity(
        axes = axes if bareme else None,
#        menage = menage,
        parent1 = parent1,
#        parent2 = parent2,
        period = periods.period('year', year),
        )
    reference_simulation = scenario.new_simulation(debug = True, reference = True)
    reform_simulation = scenario.new_simulation(debug = True)

    return reform_simulation, reference_simulation


if __name__ == '__main__':

    bareme_compare_household()
#   waterfall()
#   bareme()
#    rates()

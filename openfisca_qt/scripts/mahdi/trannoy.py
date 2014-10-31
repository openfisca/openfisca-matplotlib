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


import copy
import datetime
import sys

from openfisca_core import periods, reforms
import openfisca_france


from PyQt4.Qt import QMainWindow, QApplication
from openfisca_qt.widgets.matplotlibwidget import MatplotlibWidget


TaxBenefitSystem = openfisca_france.init_country()
tax_benefit_system = TaxBenefitSystem()


# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)


def waterfall():
    simulation = create_simulation()

    app = QApplication(sys.argv)
    win = ApplicationWindow()

    axes = win.mplwidget.axes
    title = "Mon titre"
    axes.set_title(title)
    simulation.calculate('revdisp')
    draw_waterfall(simulation, axes)
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())
#    win.mplwidget.print_figure(DESTINATION_DIR + title + '.png')


def bareme():
    simulation, reform_simulation = create_simulation(bareme = True)

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes

    simulation.calculate('revdisp')
    reform_simulation.calculate('revdisp')
    draw_bareme(
        simulation = simulation,
        axes = axes,
        x_axis = 'sal',
        reform_simulation = reform_simulation)
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def bareme_compare_household():
    simulation, reform_simulation = create_simulation(bareme = True)

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes

    simulation.calculate('revdisp')
    reform_simulation.calculate('revdisp')
    draw_bareme(
        simulation = simulation,
        axes = axes,
        x_axis = 'sal',
        reform_simulation = reform_simulation)
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())



def draw_waterfall(simulation, axes):
    currency = simulation.tax_benefit_system.CURRENCY
    from openfisca_qt.plugins.utils import OutNode
    from openfisca_qt.plugins.scenario.graph import drawWaterfall
    data = OutNode.init_from_decomposition_json(simulation = simulation, decomposiiton_json = None)
    data.setLeavesVisible()
    data['revdisp'].visible = 1
    ax = axes
    ax.clear()
    drawWaterfall(data['revdisp'], ax, currency)


def draw_bareme(simulation, axes, x_axis, reform_simulation = None):
    from openfisca_qt.plugins.utils import OutNode
    from openfisca_qt.plugins.scenario.graph import drawBareme
    currency = simulation.tax_benefit_system.CURRENCY
    if reform_simulation is not None:
        data = OutNode.init_from_decomposition_json(simulation = reform_simulation, decomposiiton_json = None)
        reference_data = OutNode.init_from_decomposition_json(simulation = simulation, decomposiiton_json = None)
        is_reform = True
        data.difference(reference_data)
    else:
        data = OutNode.init_from_decomposition_json(simulation = simulation, decomposiiton_json = None)
    data.setLeavesVisible()
    data['revdisp'].visible = 0 # TODO modify this
    data[x_axis].setHidden(changeParent = True)

    if reform_simulation is not None:
        data.hideAll()

    axes.clear()
    drawBareme(data, axes, x_axis, reform = is_reform, legend = True,
               reference_data = reference_data, currency = currency)


def create_simulation(year = 2014, bareme = False):
    parent1 = dict(
        birth = datetime.date(year - 40, 1, 1),
        sali = 4000 if bareme is False else None,
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
            count = 100,
            name = 'sali',
            max = 30000,
            min = 0,
            ),
        ]
    scenario = tax_benefit_system.new_scenario().init_single_entity(
        axes = axes,
        menage = menage,
        parent1 = parent1,
#        parent2 = parent2,
        period = periods.period('year', year),
        )
    simulation = scenario.new_simulation(debug = True)


    reference_legislation_json = tax_benefit_system.legislation_json
    reform_legislation_json = copy.deepcopy(reference_legislation_json)
    reform_legislation_json['children']['ir']['children']['bareme']['slices'][0]['rate'] = 1

    reform = reforms.Reform(
        name = "IR_100_tranche_1",
        label = u"Imposition à 100% dès le premier euro et jusqu'à la fin de la 1ère tranche",
        legislation_json = reform_legislation_json,
        reference_legislation_json = reference_legislation_json
        )

    reform_simulation = reform.new_simulation(debug = True, scenario = scenario)

    return simulation, reform_simulation

#        simulation.set_param()
#        simulation.P.ir.autre.charge_loyer.active = 1
#        simulation.P.ir.autre.charge_loyer.plaf = 1000
#        simulation.P.ir.autre.charge_loyer.plaf_nbp = 0
#        print simulation.P
#        print type(simulation.P)
#        reduc = 0
#        print simulation.P.ir.bareme
#        print len(simulation.P.ir.bareme.thresholds)
#        for i in range(2, len(simulation.P.ir.bareme.thresholds)):
#            simulation.P.ir.bareme.setSeuil(i, simulation.P.ir.bareme.thresholds[i] * (1 - reduc))
#
#        print simulation.P.ir.bareme
#        print len(simulation.P.ir.bareme.thresholds)
#
#        if simulation.reforme is True:
#            df = simulation.get_results_dataframe(difference = True)
#        else:
#            df = simulation.get_results_dataframe()
#        print df.to_string()
#
#        # Save example to excel
#        if save:
#            destination_dir = "c:/users/utilisateur/documents/"
#            if reforme:
#                fname = destination_dir + "Trannoy_reforme_new_diff.%s" % "xlsx"
#                print "Saving " + fname
#                df.to_excel(fname, sheet_name = "difference")
#            else:
#                fname = destination_dir + "Trannoy_reforme_new.%s" % "xlsx"
#                print "Saving " + fname
#                df.to_excel(fname, sheet_name = "Trannoy")


def survey_case(year):

#        fname = "Agg_%s.%s" %(str(yr), "xls")
    simulation = SurveySimulation()
    simulation.set_config(year = year, num_table = 1, reforme = True)
    simulation.set_param()
    simulation.P.ir.autre.charge_loyer.plaf = 500
    simulation.P.ir.autre.charge_loyer.active = 1
    simulation.P.ir.autre.charge_loyer.plaf_nbp = 0

    # plaf=1000 plaf_nbp=0: -42160, =1: -41292
    # plaf=500  plaf_nbp=0: -43033, =1: -42292

    # Bareme threshold reduction in pct
    reduc = .1
    print simulation.P.ir.bareme
    print len(simulation.P.ir.bareme.thresholds)
    for i in range(2, len(simulation.P.ir.bareme.thresholds)):
        simulation.P.ir.bareme.setSeuil(i, simulation.P.ir.bareme.thresholds[i] * (1 - reduc))

    print simulation.P.ir.bareme
    print len(simulation.P.ir.bareme.thresholds)
    simulation.compute()

# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()

    df1 = agg.aggr_frame
    print df1.to_string()
    return


if __name__ == '__main__':
#    survey_case(2010)
    bareme()


# -*- coding: utf-8 -*-


from __future__ import division


import datetime
import sys

try:
    from PyQt4.Qt import QMainWindow, QApplication
except ImportError:
    from PySide.QtGui import QMainWindow, QApplication

from openfisca_core import periods
from openfisca_france import FranceTaxBenefitSystem
from openfisca_matplotlib.tests.test_parametric_reform import ir_100_tranche_1


from openfisca_matplotlib.widgets.matplotlibwidget import MatplotlibWidget
from openfisca_matplotlib import graphs

tax_benefit_system = FranceTaxBenefitSystem()


class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)


def waterfall():
    simulation, _ = create_simulation()
    year = 2014
    app = QApplication(sys.argv)
    win = ApplicationWindow()

    axes = win.mplwidget.axes
    title = "Mon titre"
    axes.set_title(title)
    simulation.calculate('revenu_disponible', period = year)
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
    year = 2014
    reference_simulation.calculate('revenu_disponible', period = year)
    reform_simulation.calculate('revenu_disponible', period = year)
    graphs.draw_bareme(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'salaire_brut',  # instead of salaire_de_base
        visible_lines = ['revenu_disponible'])
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def rates(year = 2014):
    reform_simulation, reference_simulation = create_simulation(bareme = True)
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes
    graphs.draw_rates(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'salaire_de_base',
        y_axis = 'revenu_disponible',
        period = year,
        reference_simulation = reference_simulation,
        )
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def bareme_compare_household():
    simulation_1p, simulation_2p = create_simulation2(bareme = True)

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    axes = win.mplwidget.axes
    year = 2014
    simulation_1p.calculate('revenu_disponible', period = year)
    simulation_2p.calculate('revenu_disponible', period = year)
    graphs.draw_bareme(
        simulation = simulation_2p,
        axes = axes,
        x_axis = 'salaire_brut',  # instead of salaire_de_base
        reference_simulation = simulation_1p,
        visible_lines = ['revenu_disponible'],
        )
    win.resize(1400, 700)
    win.mplwidget.draw()
    win.show()
    sys.exit(app.exec_())


def create_simulation2(year = 2014, bareme = False):
    parent1 = dict(
        date_naissance = datetime.date(year - 40, 1, 1),
        salaire_de_base = 4000 if bareme is False else None,
        )
    parent2 = dict(
        date_naissance = datetime.date(year - 40, 1, 1),
        salaire_de_base = 1000,
        )
    # Adding a husband/wife on the same tax sheet (foyer)
    menage = dict(
        loyer = 1000,
        statut_occupation_logement = 4,
        )
    axes = [
        dict(
            count = 100,
            name = 'salaire_de_base',
            max = 30000,
            min = 0,
            ),
        ]
    scenario_1p = tax_benefit_system.new_scenario().init_single_entity(
        axes = axes if bareme else None,
        menage = menage,
        parent1 = parent1,
        period = periods.period(year),
        )
    simulation_1p = scenario_1p.new_simulation()

    scenario_2p = tax_benefit_system.new_scenario().init_single_entity(
        axes = axes if bareme else None,
        menage = menage,
        parent1 = parent1,
        parent2 = parent2,
        period = periods.period(year),
        )
    simulation_2p = scenario_2p.new_simulation()

    return simulation_1p, simulation_2p


def create_simulation(year = 2014, bareme = False):

    reform = ir_100_tranche_1(tax_benefit_system)
    parent1 = dict(
        date_naissance = datetime.date(year - 40, 1, 1),
        salaire_de_base = 10000 if bareme is False else None,
        categorie_salarie = 0,
        )
#    parent2 = dict(
#        date_naissance = datetime.date(year - 40, 1, 1),
#        salaire_de_base = 0,
#        )
    # Adding a husband/wife on the same tax sheet (foyer)
    menage = dict(
        loyer = 1000,
        statut_occupation_logement = 4,
        )
    axes = [
        dict(
            count = 200,
            name = 'salaire_de_base',
            max = 300000,
            min = 0,
            ),
        ]
    scenario = reform.new_scenario().init_single_entity(
        axes = axes if bareme else None,
        menage = menage,
        parent1 = parent1,
        # parent2 = parent2,
        period = periods.period(year),
        )
    reference_simulation = scenario.new_simulation(debug = True, use_baseline = True)
    reform_simulation = scenario.new_simulation(debug = True)
    return reform_simulation, reference_simulation


if __name__ == '__main__':
    # bareme_compare_household()
    # waterfall()
    # bareme()
    rates()

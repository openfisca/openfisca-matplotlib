# -*- coding: utf-8 -*-


from __future__ import division


import datetime
import sys

try:
    from PyQt4.Qt import QMainWindow, QApplication
except ImportError:
    try:
        from PySide.QtGui import QMainWindow, QApplication
    except ImportError:
        QMainWindow, QApplication = None, None
        import matplotlib.pyplot as plt

from openfisca_core import periods
from openfisca_france import FranceTaxBenefitSystem
from openfisca_matplotlib.tests.test_parametric_reform import ir_100_tranche_1


from openfisca_matplotlib.widgets.matplotlibwidget import MatplotlibWidget
from openfisca_matplotlib import graphs

tax_benefit_system = FranceTaxBenefitSystem()


def get_axes():
    if QMainWindow and QApplication:
        class ApplicationWindow(QMainWindow):
            def __init__(self):
                QMainWindow.__init__(self)
                self.mplwidget = MatplotlibWidget(self)
                self.mplwidget.setFocus()
                self.setCentralWidget(self.mplwidget)

        app = QApplication(sys.argv)
        win = ApplicationWindow()
        axes = win.mplwidget.axes
    else:
        axes = plt.axes()
        win = None
        app = None

    return axes, win, app


def post_plot(axes, win, app):
    if win is None:
        plt.show()
        del axes
        return
    else:
        win.resize(1400, 700)
        win.mplwidget.draw()
        win.show()
        sys.exit(app.exec_())


def test_waterfall():
    simulation, _ = create_simulation()
    year = 2014
    title = "Mon titre"
    axes, win, app = get_axes()
    axes.set_title(title)
    simulation.calculate('revenu_disponible', period = year)
    graphs.draw_waterfall(
        simulation = simulation,
        axes = axes,
        )
    post_plot(axes, win, app)


def test_bareme():
    reform_simulation, reference_simulation = create_simulation(bareme = True)

    axes, win, app = get_axes()
    year = 2014
    reference_simulation.calculate('revenu_disponible', period = year)
    reform_simulation.calculate('revenu_disponible', period = year)
    graphs.draw_bareme(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'salaire_brut',  # instead of salaire_de_base
        visible_lines = ['revenu_disponible'])
    post_plot(axes, win, app)


def test_rates(year = 2014):
    reform_simulation, reference_simulation = create_simulation(bareme = True)
    axes, win, app = get_axes()
    graphs.draw_rates(
        simulation = reform_simulation,
        axes = axes,
        x_axis = 'salaire_de_base',
        y_axis = 'revenu_disponible',
        period = year,
        reference_simulation = reference_simulation,
        )
    post_plot(axes, win, app)


def test_bareme_compare_household():
    simulation_1p, simulation_2p = create_simulation2(bareme = True)

    axes, win, app = get_axes()
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
    post_plot(axes, win, app)


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
        statut_occupation_logement = "locataire_vide",
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
        categorie_salarie = 'prive_non_cadre',
        )
#    parent2 = dict(
#        date_naissance = datetime.date(year - 40, 1, 1),
#        salaire_de_base = 0,
#        )
    # Adding a husband/wife on the same tax sheet (foyer)
    menage = dict(
        loyer = 1000,
        statut_occupation_logement = "locataire_vide",
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
    test_bareme_compare_household()
    test_waterfall()
    test_bareme()
    test_rates()

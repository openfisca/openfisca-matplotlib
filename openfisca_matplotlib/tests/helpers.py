# -*- coding: utf-8 -*-

from __future__ import division

import datetime


from openfisca_core import periods
from openfisca_france import FranceTaxBenefitSystem
from openfisca_matplotlib.tests.test_parametric_reform import ir_100_tranche_1

tax_benefit_system = FranceTaxBenefitSystem()


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
        period = periods.period(year),
        )
    reference_simulation = scenario.new_simulation(debug = True, use_baseline = True)
    reform_simulation = scenario.new_simulation(debug = True)
    return reform_simulation, reference_simulation
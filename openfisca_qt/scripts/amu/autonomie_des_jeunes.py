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


# Exemple of a simple simulation


import datetime

from openfisca_core import model
import openfisca_france
openfisca_france.init_country()
from openfisca_core.simulations import ScenarioSimulation


# TODO: logement


def get_couple_with_child_results_datatframe(sali_vous = 0, sali_conj = 0):
    simulation = ScenarioSimulation()
    simulation.set_config(year = 2013,
                          nmen = 1)

    # Adding a husband/wife on the same tax sheet (ie foyer, as conj) and of course same family (as part)
    simulation.scenario.addIndiv(1, datetime.date(1975, 1, 1), 'conj', 'part')

    # Adding 1 kids on the same tax sheet and family
    simulation.scenario.addIndiv(2, datetime.date(1993, 1, 1), 'pac', 'enf')

    # Changing the revenu of the parents
    scenario = simulation.scenario
    scenario.indiv[0]['sali'] = sali_vous
    scenario.indiv[1]['sali'] = sali_conj

    # Set the number of major kids in the
    scenario.declar[0]['nbJ'] = 1

    # Set legislative parameters
    simulation.set_param()

    # Compute the pandas dataframe of the household case_study
    df = simulation.get_results_dataframe()
    return df


def get_couple_without_child_results_datatframe(sali_vous = 0, sali_conj = 0, pension_alimentaire = 0):
    simulation = ScenarioSimulation()
    simulation.set_config(year = 2013,
                          nmen = 1)

    # Adding a husband/wife on the same tax sheet (ie foyer, as conj) and of course same family (as part)
    simulation.scenario.addIndiv(1, datetime.date(1975, 1, 1), 'conj', 'part')

    # Changing the revenu of the parents
    scenario = simulation.scenario
    scenario.indiv[0]['sali'] = sali_vous
    scenario.indiv[1]['sali'] = sali_conj

    # Set the number of major kids in the
    scenario.declar[0]['f6gi'] = pension_alimentaire

    # Set legislative parameters
    simulation.set_param()

    # Compute the pandas dataframe of the household case_study
    df = simulation.get_results_dataframe()
    return df


def get_child_results_datatframe(pension_alimentaire = 0):
    simulation = ScenarioSimulation()
    simulation.set_config(year = 2013,
                          nmen = 1)

    scenario = simulation.scenario

    # Set the number of major kids in the
    scenario.declar[0]['alr'] = pension_alimentaire
    # Set legislative parameters
    simulation.set_param()

    # Compute the pandas dataframe of the household case_study
    df = simulation.get_results_dataframe()
    return df


if __name__ == '__main__':

    sali_vous = 12 * 3000
    sali_conj = 12 * 3000
    pension_alimentaire = 12 * 500

    df_couple_with_child = get_couple_with_child_results_datatframe(sali_vous = sali_vous,
                                                                    sali_conj = sali_conj)

    df_couple_without_child = get_couple_without_child_results_datatframe(sali_vous = sali_vous,
                                                                       sali_conj = sali_conj,
                                                                       pension_alimentaire = pension_alimentaire)

    df_child = get_child_results_datatframe(pension_alimentaire = pension_alimentaire)


    df = (df_couple_without_child + df_child - df_couple_with_child)
    print df.to_string()

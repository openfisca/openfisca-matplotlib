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



def get_couple_results_dataframe(sali_vous_maxrev = 12 * 4000, sali_conj = 12 * 2000, nmen = 11):

    # Creating a case_study household with one individual whose taxable income (salaire imposable, sali
    # varies from 0 to maxrev = 100000 in nmen = 3 steps
    simulation = ScenarioSimulation()
    simulation.set_config(year = 2013,
                          nmen = nmen,
                          maxrev = sali_vous_maxrev,
                          x_axis = 'sali')

    # Adding a husband/wife on the same tax sheet (ie foyer, as conj) and of course same family (as part)
    simulation.scenario.addIndiv(1, datetime.date(1975, 1, 1), 'conj', 'part')
    simulation.scenario.indiv[1]['sali'] = sali_conj

    # Set legislative parameters
    simulation.set_param()

    df = simulation.get_results_dataframe()

    df2 = df.transpose()[['Salaires imposables', u'Impôt sur le revenu']]
    df2['Salaires imposables vous'] = df2['Salaires imposables'] - sali_conj
    df2['Salaires imposables conj'] = sali_conj

    return df2


if __name__ == '__main__':

    df = get_couple_results_dataframe()
    print df.to_string()

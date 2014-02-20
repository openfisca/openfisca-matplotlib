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


def case_study(year = 2013):

    # Creating a case_study household with one individual whose taxable income (salaire imposable, sali
    # varies from 0 to maxrev = 100000 in nmen = 3 steps

    simulation = ScenarioSimulation()

    simulation.set_config(year = 2013,
                          nmen = 11,
                          maxrev = 10000,
                          x_axis = 'sali')

    print simulation.scenario

    simulation.scenario.addIndiv(1, datetime.date(1975, 1, 1), 'conj', 'part')

    print simulation.scenario

    simulation.set_param()  # Va chercher la legislation par défaut

    df = simulation.get_results_dataframe()

    print df.to_string()

    print simulation.input_table.table.to_string()
    print simulation.output_table.table.to_string()



if __name__ == '__main__':

    case_study()

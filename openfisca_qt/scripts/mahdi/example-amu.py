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


from datetime import datetime

from openfisca_core import model
import openfisca_france
openfisca_france.init_country()
from openfisca_core.simulations import ScenarioSimulation


def case_study(year = 2013):

    # Creating a case_study household with one individual whose taxable income (salaire imposable, sali
    # varies from 0 to maxrev = 100000 in nmen = 3 steps
    simulation = ScenarioSimulation()
    simulation.set_config(year = year,
                          reforme = True,
                          nmen = 11,
                          maxrev = 100000,
                          x_axis = 'sali')

    print simulation.
    # Adding a husband/wife on the same tax sheet (ie foyer, as conj) and of course same family (as part)
    simulation.scenario.addIndiv(1, datetime(1975, 1, 1).date(), 'conj', 'part')

    # Adding 3 kids on the same tax sheet and family
    simulation.scenario.addIndiv(2, datetime(2001, 1, 1).date(), 'pac', 'enf')
    simulation.scenario.addIndiv(3, datetime(2002, 1, 1).date(), 'pac', 'enf')
    simulation.scenario.addIndiv(4, datetime(2003, 1, 1).date(), 'pac', 'enf')

    # Set legislative parameters
    simulation.set_param()

    # Some prestation can be disabled (herethe aefa prestation) by uncommenting the following line
    # simulation.disable_prestations( ['aefa'])

    # Performing a parameterical reform (inspect openifsca-country.param.param.xml)
    # Lower the part in the quotient familial for the third child from 1 to .5

    print 'default value for P.ir.quotient_familial.enf2 : %s \n' % simulation.P.ir.quotient_familial.enf2
    simulation.P.ir.quotient_familial.enf2 = 0
    print 'reform value for P.ir.quotient_familial.enf2 : %s \n' % simulation.P.ir.quotient_familial.enf2


    # Compute the pandas dataframe of the household case_study
    df = simulation.get_results_dataframe(default = True)
    print df.to_string()

    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")
    # df.to_excel(destination_dir = "c:/users/utilisateur/documents/" + fname)

    df_reform = simulation.get_results_dataframe()
    print df_reform.to_string()


    # Many other variables are accessible
    # Input variables
    print 'list of input variables : %s \n' % simulation.input_var_list
    # Getting the value of some input variables
    print simulation.input_table.table['so']

    # Output variables
    print 'list of output variables : %s \n' % simulation.output_var_list
    print simulation.output_table.table['ir_plaf_qf']
    print simulation.output_table_default.table['ir_plaf_qf']
    #


if __name__ == '__main__':
    case_study()

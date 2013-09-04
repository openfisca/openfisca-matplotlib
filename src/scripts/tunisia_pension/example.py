# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simulation

from src.lib.simulation import ScenarioSimulation

from datetime import datetime


def test_case(year):
    
    country = 'tunisia_pension'
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=False,
                    nmen = 3, maxrev = 10000, xaxis = 'sal0')
    # Adding a husband/wife on the same tax sheet (foyer)

    
    simulation.set_param()
    df = simulation.get_results_dataframe()
    print df.to_string()
    
    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")    
    # df.to_excel(destination_dir = destination_dir + fname)

if __name__ == '__main__':
    test_case(2010)


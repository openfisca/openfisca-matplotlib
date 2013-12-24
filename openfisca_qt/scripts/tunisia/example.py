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
    
    country = 'tunisia'
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=False,
                    nmen = 3, maxrev = 12*400, xaxis = 'sali')
    # Adding a husband/wife on the same tax sheet (foyer)
    simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
    
    simulation.scenario.addIndiv(2, datetime(2000,1,1).date(), 'pac', 'enf') 
    simulation.scenario.addIndiv(3, datetime(2000,1,1).date(), 'pac', 'enf')
    
    simulation.set_param()
    df = simulation.get_results_dataframe()
    print df.to_string()
    
    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")    
    # df.to_excel(destination_dir = destination_dir + fname)

if __name__ == '__main__':
    test_case(2011)


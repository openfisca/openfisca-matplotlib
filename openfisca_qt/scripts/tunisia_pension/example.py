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
country = 'tunisia_pension'

def test_case(year):

    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=False,
                    nmen = 4, maxrev = 25*9*12*3, xaxis = 'sal0')
    # Adding a husband/wife on the same tax sheet (foyer)

    
    simulation.set_param()
    df = simulation.get_results_dataframe()
    print df.to_string()
    
    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")    
    # df.to_excel(destination_dir = destination_dir + fname)


def test_case_reform(year):
    """
    A test case with reform
    """
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=True, nmen = 1)
    # Adding a husband/wife on the same tax sheet (foyer)

    simulation.set_param()
    test_case = simulation.scenario
    
    sal_mensuel = 1000
    for i in range(10): 
        test_case.indiv[0].update({"sal" + str(i): sal_mensuel*12})
    
    
    test_case.indiv[0].update({"nb_trim_val": 50})
    test_case.indiv[0].update({"age": 54})
    simulation.set_param()
    
    print simulation.P_default
    param =  simulation.P
    # param.pension.rsna.taux_ann_base = .03
    param.pension.rsna.age_dep_anticip = 55
        
    df = simulation.get_results_dataframe()
    print df.to_string()



if __name__ == '__main__':
    test_case_reform(2011)


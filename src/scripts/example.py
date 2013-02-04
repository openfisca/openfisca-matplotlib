# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simualtion

from src.core.simulation import ScenarioSimulation 


if __name__ == '__main__':

    yr = 2009
    country = 'france'

    simu = ScenarioSimulation()
    simu.set_config(year = yr, country = country, 
                    nmen = 1, maxrev = 100000, xaxis = 'sali')
    simu.set_param()
#    simu.disable_prestations( ['aefa'])
    df = simu.get_results_dataframe()

    print df.to_string()

    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")    
    # df.to_excel(destination_dir = "c:/users/utilisateur/documents/" + fname)


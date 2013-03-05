# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simualtion

from src.lib.simulation import ScenarioSimulation 

from src.lib.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates
from pandas import ExcelWriter
import os

country = 'france'
destination_dir = "c:/users/utilisateur/documents/"
fname_all = "aggregates_inflated_loyers.xlsx"
fname_all = os.path.join(destination_dir, fname_all)              



def test_case():
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


def survey_case():
    
    year = 2006 
    yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
    simu = SurveySimulation()
    simu.set_config(year = yr, country = country)
    simu.set_param()
    simu.set_survey()

#    inflator = get_loyer_inflator(year)
#    simu.inflate_survey({'loyer' : inflator})
#    simu.compute()
#    
#    agg = Aggregates()
#    agg.set_simulation(simu)
#    agg.compute()
#
#    if writer is None:
#        writer = ExcelWriter(str(fname_all))
#    agg.aggr_frame.to_excel(writer, yr, index= False, header= True)
#    del simu
#    del agg
#    import gc
#    gc.collect()

    
    

if __name__ == '__main__':

    survey_case()

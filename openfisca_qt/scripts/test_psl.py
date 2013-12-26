# -*- coding:utf-8 -*-
# Created on 5 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Script to compute the aggregates for all the referenced years

from openfisca_core.simulations import SurveySimulation 
from openfisca_core import model
import os
country = 'france'


from src.plugins.survey.distribution import OpenfiscaPivotTable

def get_age_structure(simulation):
    
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df = pivot_table.get_table(entity = 'ind', by = "age", vars = [])
    return df

def get_structure(simulation, by_var):
    
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df = pivot_table.get_table(entity = 'ind', by = by_var, vars = [], champm=False)
    return df


def test():
    yr = 2006
    country = 'france'
    simu = SurveySimulation()
    simu.set_config(year = yr, country = country)
    simu.set_param()
    filename = os.path.join(model.DATA_DIR, 'survey_psl.h5')
    simu.set_survey(filename = filename)
    simu.compute()
    
    df = get_structure(simu, 'br_al')
    print df.to_string()    

    
if __name__ == '__main__':
    

#    build_aggregates()
#    diag_aggregates()
    test()

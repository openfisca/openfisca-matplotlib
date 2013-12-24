# -*- coding:utf-8 -*-
# Created on 5 juil. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Author: Victor Le Breton

from src.lib.simulation import SurveySimulation, load_content, Simulation, ScenarioSimulation
import os
from src import SRC_PATH

if __name__ == "__main__":    
    
    # Code pour tester save_content
    yr = 2006
    country = 'france'
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=yr, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()
    simulation.compute()
    print simulation.__dict__.keys()
            
    print simulation.output_table.__dict__.keys()
    print 'done'
    simulation.save_content('testundeux', 'fichiertestundeux')

    a = load_content('testundeux', 'fichiertestundeux')
    print a.output_table.description.columns
    print a.input_table.table['idfoy'][0:50]
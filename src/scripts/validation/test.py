# -*- coding:utf-8 -*-
# Created on 21 mars 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from src.lib.simulation import SurveySimulation

import nose

# Validation
# Should ideally produce a log file 
# Try to be the most country/model 
# agnostic (so part of the general stuff could be elsewhere
# Proceed using import from separate file in validation

year = 2006
country = "france"
simulation = SurveySimulation()
simulation.set_config(year = year, country = country)
simulation.set_param()
simulation.set_survey()

# Pre-computation validation
# 
   
from src.scripts.validation.check_consistency_tests import ( check_inputs_enumcols,
                                                              check_entities,
                                                              check_weights)

def test_inputs_consistency():
    """ 
    Test consistency of inputs data
    """

#    check that the Enumcols are right (and fix the labels/the original data)
    ok, message = check_inputs_enumcols(simulation)
    if not ok: 
        print "Error: Check enumcols"
    
    assert ok == True

    
    #    check the validity of men/foy/fam  see check_consistency_test
    ok, message = check_entities(simulation)
    if not ok: 
        print "Error: Check entities"
        print message       
    assert ok == True
    
    #    check of positiveness of the variable that should be ?
    ok, message = check_weights(simulation)
    if not ok: 
        print "Error: Check weights"
        print message
        
    assert ok == True




if __name__ == '__main__':
    nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])
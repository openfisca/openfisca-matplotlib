# -*- coding:utf-8 -*-
# Created on 21 mars 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from src.lib.simulation import SurveySimulation

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
# Validation of input data 
#  Consistency of declared data
#    check that the Enumcols are right (and fix the labels/the original data)
   
from src.scripts.validation.check_consistency_tests import ( check_inputs_enumcols,
                                                              check_entities,
                                                              check_weights)

if not check_inputs_enumcols(simulation):
    print "Error: Check enumcols"

#    check the validity of men/foy/fam  see check_consistency_test
if not check_entities(simulation):
    print "Error: Check entities"

#    check of positiveness of the variable that should be ?
if not check_weights(simulation):
    print "Error: Check weights"

#  Demographic characteristics
#    number of households/foyers compared to erf (and other sources recensement ? careful with champm variable)
#    types of household compared to erf
#    age structure of population  scripts.sandbox.age_structure.py

# Post-computation validation
#
#  Check for every prestation the equivalence/differneces of concept definition
#  Decompose cotsoc (in the code TODO: MBJ LB ?)
#  Decompose impot sur le revenu to check intermediate aggregates vs fiscal data and erf
#  Check downward prestation one by one


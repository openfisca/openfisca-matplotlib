# -*- coding:utf-8 -*-
# Created on 17 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from src.lib.simulation import SurveySimulation 
from src.lib.utils import of_import
from pandas import concat

def check_entities(simulation):

    is_ok = True
    survey = simulation.survey

    ENTITIES_INDEX = of_import(None, "ENTITIES_INDEX", country = simulation.country)

    for entity in ENTITIES_INDEX:
                
        id = survey.table['id' + entity]
        head = survey.table['qui' + entity]
        
        df = concat([id, head],axis=1)
        grouped_by_id = df.groupby(id)
        
        def is_there_head(group):
            dummy = (group == 0).sum()
            return dummy
        
        headcount = grouped_by_id["qui"+entity].aggregate({entity + " heads" : is_there_head})
        result =  headcount[headcount[entity + " heads"] != 1]  
        
        if len(result) != 0:
            is_ok = False

    return is_ok




from src.lib.columns import EnumCol
def check_inputs_enumcols(simulation):
    """
    Check that the enumcols are consistent
    with data in the survey dataframe
    
    Parameters
    ----------
    
    simulation : SurveySimulation
                 The simulation to check
    
    Returns :
    
    is_ok : bool
            True or False according to tests
    """
    
    # TODO: eventually should be a method of SurveySimulation specific for france 
    
    is_ok = True
    survey = simulation.survey
    for var in survey.col_names:
        varcol  = survey.description.get_col(var)
        if isinstance(varcol, EnumCol):
            try:
                x = sorted(varcol.enum._nums.values())
                if set(survey.table[var].unique()) > set(varcol.enum._nums.values()):
                    print var
                    print "Wrong nums"
                    print varcol.enum._nums
                    print sorted(survey.table[var].unique())
                    is_ok = False
            except:
                is_ok = False
                print var
                print "Wrong nums"
                print varcol.enum
                print sorted(survey.table[var].unique())
                print "\n"

            try:
                x = varcol.enum._vars
            except:
                is_ok = False
                print var
                print "wrong vars"
                print varcol.enum
                print sorted(survey.table[var].unique())
                print "\n"
    
    return is_ok

def check_weights(simulation):
    """
    Check weights positiveness
    
    Parameters
    ----------
    
    simulation : SurveySimulation
                 The simulation to check
    
    Returns :
    
    is_ok : bool
            True or False according to tests
    """
    is_ok = True
    survey = simulation.survey
    WEIGHT = of_import(classname="WEIGHT", country=simulation.country)
    weight = survey.get_value(WEIGHT)
    if sum(weight<=0) != 0:
        is_ok = False
    return is_ok

def toto(simulation):
    survey = simulation.survey        
    # verifying the age of childrens
    quifam = survey.get_value('quifam')
    age = survey.get_value('age')
    if sum((quifam >= 2) & (age >= 21)) != 0:
        print "they are kids that are of age >= 21"


    # Problemes
    # enfants de plus de 21 ans et parents à charge dans les familles avec quifam=0

#    idmen = survey.get_value('idmen')
#    from numpy import max as max_
#    print max_(idmen)


                        
if __name__ == '__main__':
    year = 2006
    country = "france"
    simulation = SurveySimulation()
    simulation.set_config(year = year, country = country)
    simulation.set_param()
    simulation.set_survey()
    # print check_inputs_enumcols(simulation)
    check_entities(simulation)
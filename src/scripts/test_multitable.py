# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


'''
Created on 9 juil. 2013

@author: Jérôme SANTOUL
'''

from src.lib.simulation import ScenarioSimulation
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from datetime import datetime
from pandas import ExcelWriter, HDFStore
import os
from src.countries.france.data.erf.aggregates import build_erf_aggregates
import pandas as pd
from src import SRC_PATH
from src.countries.france.data.erf.build_survey.utilitaries import check_structure

country = 'france'

def vars_matching_entity_from_table(table, simulation=None, entity='ind'):
    """
    Extract simulation input variables which entity attribute matches entity
    from table 
    """
    if simulation is None:
        raise Exception('You need a simulation to extract the variables from')
    
    vars_matching_entity = ['quifoy', 'quifam','quimen'] #TODO: faire qqchose de plus propre
    for var in simulation.input_var_list:  
        if var in table.columns:
            col = simulation.get_col(var)
            if col.entity == entity:
                vars_matching_entity.append(str(var))
    return vars_matching_entity


def test_convert_to_3_tables(year=2006):
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    filename3 = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')
    store = HDFStore(survey_filename)
    print store
    
    output = HDFStore(filename3)
    print output
    
    from src.lib.simulation import SurveySimulation
    simulation = SurveySimulation()
    simulation.set_config(country="france", year=year)
    
    table1 = store['survey_'+str(year)]   
    print table1
    

    for entity in ['ind','foy','men','fam']:
        key = 'survey_'+str(year) + '/'+str(entity)
        
        vars_matching_entity = vars_matching_entity_from_table(table1, simulation, entity)
        print entity, vars_matching_entity_from_table
        if entity == 'ind': 
            table_entity = table1[vars_matching_entity]
        # we take care have all ident and selecting qui==0
        else:
            enum = 'qui'+entity
            table_entity = table1.ix[table1[enum] ==0 ,['noi','idmen','idfoy','idfam'] + 
                                                        vars_matching_entity]
            table_entity= table_entity.rename_axis(table_entity['id'+entity], axis=1)
        print key
        output.put(key, table_entity)
    
    df_fam = output['survey_2006/fam']
    df_foy = output['survey_2006/foy']
    df_men = output['survey_2006/men']
    
    
    df_foy['noindiv'] = df_foy['noi'] ; del df_foy['noi']
    df_fam['noindiv'] = df_fam['noi'] ; del df_fam['noi']
    df_men['noindiv'] = df_men['noi'] ; del df_men['noi']
    
#     print df_fam, df_foy, df_men
    check_structure(df_foy)
    check_structure(df_fam)
    check_structure(df_men)
    check_structure(store['survey_2006'])

    del table1
    
    import gc
    gc.collect()
    store.close()
    output.close()

if __name__ == '__main__':
    test_convert_to_3_tables()
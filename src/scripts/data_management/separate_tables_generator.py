# -*- coding:utf-8 -*-
'''
Created on 9 juil. 2013

@author: Utilisateur
'''
from src import SRC_PATH
import os
from pandas import HDFStore
from src.lib.simulation import SurveySimulation

country = "france"


def vars_matching_entity_from_table(table, simulation=None, entity='ind'):
    """
    Extract simulation input variables which entity attribute matches entity
    from table 
    """
    if simulation is None:
        raise Exception('You need a simulation to extract the variables from')
    
    vars_matching_entity = []
        
    for var in simulation.input_var_list:  
        if var in table.columns:
            col = simulation.get_col(var)
            if col.entity == entity:
                vars_matching_entity.append(str(var))
    return vars_matching_entity


def convert_to_3_tables(year=2006, survey_file=None, output_file=None):
    
    if survey_file is None:
        raise Exception('You need a .h5 file with the survey to extract the variables from')
    if output_file is None:
        output_file = survey_file
        raise Warning('the survey file will be used to store the created tables')
    
    store = HDFStore(survey_file)
    output = HDFStore(output_file)
    print output
    
    simulation = SurveySimulation()
    simulation.set_config(country="france", year=year)
    table1 = store['survey_'+str(year)]   

    for entity in ['ind','foy','men','fam']:
        key = 'survey_'+str(year) + '/'+str(entity)
        
        vars_matching_entity = vars_matching_entity_from_table(table1, simulation, entity)
        print entity, vars_matching_entity_from_table
        print 'table1 enum'
        
        if entity == 'ind': 
            print 'INDIVIDUALS'
            print table1['noindiv']
            table_entity = table1.loc[:, vars_matching_entity]
            
        # we take care have all ident and selecting qui==0
        else:
#             print '    entity :', entity
#             print table1['noindiv'].head()
            position = 'qui'+entity
#             print table1[position]
            table_entity = table1.ix[table1[position] == 0 ,['noi','idmen','idfoy','idfam','quifoy','quimen','quifam'] + 
                                                        vars_matching_entity]
#             print table_entity.noi.head()
            table_entity= table_entity.rename_axis(table_entity['id'+entity], axis=1)
#             print '    APRES'
#             print table_entity.noi.head()
        print key
        output.put(key, table_entity)
    
    del table1
    import gc
    gc.collect()

    store.close()
    output.close()

if __name__ == '__main__':
    convert_to_3_tables()
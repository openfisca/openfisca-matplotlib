'''
Created on 9 juil. 2013

@author: Utilisateur
'''
from src import SRC_PATH
import os
from pandas import HDFStore
country = "france"

def vars_matching_entity_from_table(table, simulation=None, entity='ind'):
    """
    Extract simulation input variables which entity attribute matches entity
    from table 
    """
    vars_matching_entity = []
    for var in simulation.input_var_list:  
        if var in table.columns:
            col = simulation.get_col(var)
            if col.entity == entity:
                vars_matching_entity.append(str(var))
    return vars_matching_entity


def convert_to_3_tables(year=2006):
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    filename3 = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')
    store = HDFStore(survey_filename)
    print store
    
    output = HDFStore(filename3)
    
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
    
    del table1
    import gc
    gc.collect()

    store.close()
    output.close()



if __name__ == '__main__':
    pass
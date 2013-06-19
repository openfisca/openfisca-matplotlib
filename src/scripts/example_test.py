# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simulation

from src.lib.simulation import ScenarioSimulation
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from datetime import datetime
from pandas import ExcelWriter, HDFStore
import os


country = 'france'
# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)              

from src import SRC_PATH
    

def survey_case():
    year = 2006 
    yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=yr, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()


#    Ignore this
#    inflator = get_loyer_inflator(year)
#    simulation.inflate_survey({'loyer' : inflator})

    simulation.compute()
    simul_out_df = simulation.output_table.table
    print simul_out_df.loc[:,['af', 'af_base']].describe()
    print simul_out_df.columns
    
    return
# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()
    
    df1 = agg.aggr_frame
    print df1.to_string()
    
#    Saving aggregates
#    if writer is None:
#        writer = ExcelWriter(str(fname)
#    agg.aggr_frame.to_excel(writer, yr, index= False, header= True)


# Displaying a pivot table    
    from src.plugins.survey.distribution import OpenfiscaPivotTable
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df2 = pivot_table.get_table(by ='so', vars=['nivvie']) 
    print df2.to_string()



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
    survey_case()
#     convert_to_3_tables()

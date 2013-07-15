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
from src.countries.france.data.erf.aggregates import build_erf_aggregates
import pandas as pd

try:
    import xlwt
    from src.countries.france.XL import XLtable
except:
    pass



# from src.scripts.validation.check_consistency_tests import ( check_inputs_enumcols,
#                                                               check_entities,
#                                                               check_weights)

country = 'france'
# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)              

from src import SRC_PATH


def survey_case(year = 2006): 
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
    simul_in_df = simulation.input_table.table
    print simul_out_df.loc[:,['af', 'af_base', 'af_forf', 'af_majo', 'af_nbenf']].describe()
    print 'input vars'
    print simul_in_df.columns    
    print 'output vars'
    print simul_out_df.columns
    
#     check_inputs_enumcols(simulation)
    
# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()
    df1 = agg.aggr_frame
    print df1.columns
    
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
    return df1
    

            
def test_laurence():
    import gc
    def reshape_tables(dfs, dfs_erf):
        agg = Aggregates()
        agg.set_header_labels() # We need this for the columns labels to work
        
        # Resetting index to avoid later trouble on manipulation
        for d in dfs:
            d.reset_index(inplace = True)
        for d in dfs_erf:
            d.reset_index(inplace = True)
            d['Mesure'] = agg.labels['dep']
            
    #         d.set_index( agg.labels['var'], inplace = True) #, drop = True ?
#         temp = dfs[0].merge(dfs[1], on = agg.labels['var'], suffixes = ('_2006','_2007'))
#         temp = temp.merge(dfs[2], on = agg.labels['var'], suffixes = ('_2007','_2008'))
#         temp = temp.merge(dfs[3], on = agg.labels['var'], suffixes = ('_2008','_2009'))
        temp = pd.concat([dfs[0],dfs[1]], ignore_index = True)
        temp = pd.concat([temp,dfs[2]], ignore_index = True)
        temp = pd.concat([temp,dfs[3]], ignore_index = True)
        
        # We split the real aggregates from the of table
        temp2 = temp[[agg.labels['var'], agg.labels['benef_real'], agg.labels['dep_real'], 'year']]
        del temp[agg.labels['benef_real']], temp[agg.labels['dep_real']]
        temp['source'] = 'of'
        temp2['source'] = 'reel'
        temp2.rename(columns = {agg.labels['benef_real'] : agg.labels['benef'],
                                agg.labels['dep_real'] : agg.labels['dep']}, 
                     inplace = True)
        temp = pd.concat([temp,temp2], ignore_index = True)
        
        temp3 = pd.concat([dfs_erf[0], dfs_erf[1]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[2]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[3]], ignore_index = True)
        temp3.rename(columns = var2label, inplace = True)
        temp3 = temp3.T
        temp3.reset_index(inplace = True)
        temp3.rename(columns = {'1' : agg.labels['var'], '2' : agg.labels['dep']}, inplace = True)
        temp3['source'] = 'erfs'
        
        temp = pd.concat([temp, temp3], ignore_index = True)
#         temp.set_index(agg.labels['var'], inplace = True, drop = False)
        print temp.to_string()
        
        # Index manipulation to reshape the output
        temp.reset_index(drop = True, inplace = True)
#         index = pd.MultiIndex.from_arrays([temp['Mesure'], temp['source'], temp['year']])
        temp.set_index('Mesure', drop = True, inplace = True)
        temp.set_index('source', drop = True, append = True, inplace = True)
        temp.set_index('year', drop = True, append = True, inplace = True)
        print isinstance(temp, pd.DataFrame)
#         temp = temp.pivot(columns = 'year')
        temp = temp.unstack('year')
        print temp.to_string()
#         temp = temp.stack(agg.labels['var'], dropna = False)
        temp.fillna(0, inplace = True)
        return temp

    def save_as_xls(df):
        stxl = XLtable(df)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('resultatstest')
        erfxcel = stxl.place_table(ws)
        wb.save("C:\outputtest.xls")

    dfs = []
    dfs_erf = []
    for i in range(2006,2010):
        year = i
        yr = str(i)
        # Running a standard SurveySim to get aggregates
        simulation = SurveySimulation()
        survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
        simulation.set_config(year=yr, country=country, 
                              survey_filename=survey_filename)
        simulation.set_param()
        simulation.compute()
        agg = Aggregates()
        agg.set_simulation(simulation)
        agg.compute()
        df = agg.aggr_frame
        df['year'] = year
        label2var, var2label, var2enum = simulation.output_table.description.builds_dicts()
        dfs.append(df)
        variables = agg.varlist
        print agg
        return
        del simulation, agg, label2var, var2enum
        
        #Getting ERF aggregates from ERF table
        dfs_erf.append(build_erf_aggregates(variables=variables, year= year))
        (dfs_erf[i - 2006])['year'] = year
        gc.collect()

    datatest = reshape_tables(dfs, dfs_erf)
    save_as_xls(datatest)
       
        
if __name__ == '__main__':
#     survey_case(year = 2006)
#     convert_to_3_tables()
    test_laurence()
#     year = 2006
#     dfs_erf = build_erf_aggregates(variables =["af"], year=year)
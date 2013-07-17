# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simulation

from src.lib.simulation import ScenarioSimulation, SurveySimulation, Simulation
from src.plugins.survey.aggregates import Aggregates
from datetime import datetime
from pandas import ExcelWriter, HDFStore
import os
from src.countries.france.data.erf.aggregates import build_erf_aggregates
import pandas as pd
from src.lib.utils import of_import
from pandas import DataFrame
# DataFrame.groupby(self, by, axis, level, as_index, sort, group_keys)
# DataFrame.unstack(self, level)
from pandas.core.index import Index
import numpy as np
import gc
import random

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
    '''
    Computes the openfisca/real numbers comparaison table in excel worksheet.
    
    Warning: To add more years you'll have to twitch the code manually. 
    Default is years 2006 to 2009 included.
    '''
#     from numpy.random import randn
#     mesures = ['cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add', 
#                'cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add', 
#                'cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add']
#     sources = ['of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel',
#                'of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel',
#                'of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel']
#     year = ['2006', '2006', '2006', '2006', '2006', '2006', '2006', '2006', '2006',
#             '2007', '2007', '2007', '2007', '2007', '2007', '2007', '2007', '2007',
#             '2008', '2008', '2008', '2008', '2008', '2008', '2008', '2008', '2008',
#             '2009', '2009', '2009', '2009', '2009', '2009', '2009', '2009', '2009']
#     ind = zip(*[mesures,sources, year])
# #     print ind
#     from pandas.core.index import MultiIndex
#     ind = MultiIndex.from_tuples(ind, names = ['mesure', 'source', 'year'])
# #     print ind
#     d = pd.DataFrame(randn(27,2), columns = ['A', 'B'], index = ind)
#     d_unstacked = d.unstack()
#     print d
#     indtemp1 = d.index.get_level_values(0)
#     indtemp2 = d.index.get_level_values(1)
#     indexi = zip(*[indtemp1, indtemp2])
#     print indexi
#     indexi = MultiIndex.from_tuples(indexi, names = ['Mesure', 'source'])
#     print indexi
# #     d_unstacked = d_unstacked.reindex_axis(indexi, axis = 0)
#     print d_unstacked.columns.get
#     return
    
    def reshape_tables(dfs, dfs_erf):
        agg = Aggregates()
        agg.varlist = of_import("","AGGREGATES_DEFAULT_VARS", 'france')
         
        # We need this for the columns labels to work
        
        print 'Resetting index to avoid later trouble on manipulation'
        for d in dfs:
            d.reset_index(inplace = True)
            d.set_index('Mesure', inplace = True, drop = False)
            d.reindex_axis(labels_variables, axis = 0)
            d.reset_index(inplace = True, drop = True)
#             print d.to_string()
        for d in dfs_erf:
            d.reset_index(inplace = True)
            d['Mesure'] = agg.labels['dep']
            d.set_index('index', inplace = True, drop = False)
            d.reindex_axis(agg.labels.values(), axis = 0)
            d.reset_index(inplace = True, drop = True)
#             print d.to_string()
            
        # Concatening the openfisca tables for =/= years
        temp = pd.concat([dfs[0],dfs[1]], ignore_index = True)
        temp = pd.concat([temp,dfs[2]], ignore_index = True)
        temp = pd.concat([temp,dfs[3]], ignore_index = True)
        del temp[agg.labels['entity']], temp['index']
        gc.collect()
        
        print 'We split the real aggregates from the of table'
        temp2 = temp[[agg.labels['var'], agg.labels['benef_real'], agg.labels['dep_real'], 'year']]
        del temp[agg.labels['benef_real']], temp[agg.labels['dep_real']]
        temp['source'] = 'of'
        temp2['source'] = 'reel'
        temp2.rename(columns = {agg.labels['benef_real'] : agg.labels['benef'],
                                agg.labels['dep_real'] : agg.labels['dep']}, 
                     inplace = True)
        temp = pd.concat([temp,temp2], ignore_index = True)
        
        print 'We add the erf data to the table'
        for df in dfs_erf:
            del df['level_0'], df['Mesure']
            df.rename(columns = {'index' : agg.labels['var'], 1 : agg.labels['dep']}, inplace = True)
        temp3 = pd.concat([dfs_erf[0], dfs_erf[1]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[2]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[3]], ignore_index = True)
        temp3['source'] = 'erfs'
        gc.collect()
        temp = pd.concat([temp, temp3], ignore_index = True)
#         print temp.to_string()
        
        print 'Index manipulation to reshape the output'
        temp.reset_index(drop = True, inplace = True)
        # We set the new index
#         temp.set_index('Mesure', drop = True, inplace = True)
#         temp.set_index('source', drop = True, append = True, inplace = True)
#         temp.set_index('year', drop = False, append = True, inplace = True)
        temp = temp.groupby(by=["Mesure", "source", "year"], sort = False).sum()
        # Tricky, the [mesure, source, year] index is unique so sum() will return the only value
        # Groupby automatically deleted the source, mesure... columns and added them to index
        assert(isinstance(temp, pd.DataFrame))
#         print temp.to_string()
        
        # We want the years to be in columns, so we use unstack
        temp_unstacked = temp.unstack()
        # Unfortunately, unstack automatically sorts rows and columns, we have to reindex the table :
        
        ## Reindexing rows
        from pandas.core.index import MultiIndex
        indtemp1 = temp.index.get_level_values(0)
        indtemp2 = temp.index.get_level_values(1)
        indexi = zip(*[indtemp1, indtemp2])
        indexi_bis = []
        for i in xrange(0,len(indexi)):
            if indexi[i] not in indexi_bis:
                indexi_bis.append(indexi[i])
        indexi = indexi_bis
        del indexi_bis
        indexi = MultiIndex.from_tuples(indexi, names = ['Mesure', 'source'])
#         import pdb
#         pdb.set_trace()
        temp_unstacked = temp_unstacked.reindex_axis(indexi, axis = 0)
        
        ## Reindexing columns
        col_indexi = []
        for col in temp_unstacked.columns.get_level_values(0).unique():
            for yr in temp_unstacked.columns.get_level_values(1).unique():
                col_indexi.append((col, str(yr)))
        col_indexi = MultiIndex.from_tuples(col_indexi)
#         print col_indexi
#         print temp_unstacked.columns
        print agg.labels.values()
        temp_unstacked = temp_unstacked.reindex_axis(agg.labels.values(), level = 0, axis = 1)
        
        # Our table is ready to be turned to Excel worksheet !
        print temp_unstacked.to_string()
        temp_unstacked.fillna(0, inplace = True)
        return temp_unstacked

    def save_as_xls(df):
        # Saves a datatable under Excel table using XLtable
        stxl = XLtable(df)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('resultatstest')
        erfxcel = stxl.place_table(ws)
        try: # I dunno more clever commands
            wb.save("C:\outputtest.xls")
        except:
            n = random.randint(0,100)
            wb.save("C:\outputtest_"+str(n)+".xls")

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
        colonnes = simulation.output_table.table.columns
        dfs.append(df)
        variables = agg.varlist
        labels_variables = map(lambda x: var2label[x], variables)
        del simulation, agg, var2enum, df
        gc.collect()
        
        #Getting ERF aggregates from ERF table
        temp = (build_erf_aggregates(variables=variables, year= year))
        temp.rename(columns = var2label, inplace = True)
        temp = temp.T
        temp.reset_index(inplace = True)
        temp['year'] = year
        dfs_erf.append(temp)
        del temp
        gc.collect()
        print 'Out of data fetching for year ' + str(year)
    print 'Out of data fetching'
    
    datatest = reshape_tables(dfs, dfs_erf)
    save_as_xls(datatest)
       
        
if __name__ == '__main__':
#     survey_case(year = 2006)
#     convert_to_3_tables()
    test_laurence()
#     year = 2006
#     dfs_erf = build_erf_aggregates(variables =["af"], year=year)
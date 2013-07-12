# -*- coding:utf-8 -*-
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
from src.scripts.data_management.separate_tables_generator import convert_to_3_tables
import pandas as pd
from src import SRC_PATH
from src.countries.france.data.erf.build_survey.utilitaries import check_structure, control



country = 'france'

#Setting the files path:
survey_test = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
survey3_test = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')
survey_file = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey.h5')
survey3_file = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey3.h5')


def test_convert_to_3_tables(year=2006):
    
    #Performing the separation :
    convert_to_3_tables(year=year, survey_file=survey_test, output_file=survey3_test)
    import gc
    gc.collect()
    
def check_converted():
    #Retrieving the input and output files for analysis : 
    store = HDFStore(survey_test)
    input_df = store['survey_2006']
    
    output = HDFStore(survey3_test)
    
    df_fam = output['survey_2006/fam']
    df_foy = output['survey_2006/foy']
    df_men = output['survey_2006/men']
    df_ind = output['survey_2006/ind']
    
    print input_df.columns
    print df_fam.columns
#     df_foy['noindiv'] = df_foy['noi'] ; del df_foy['noi']
#     df_fam['noindiv'] = df_fam['noi'] ; del df_fam['noi']
#     df_men['noindiv'] = df_men['noi'] ; del df_men['noi']
#     print df_fam, df_foy, df_men

#     check_structure(store['survey_2006'])
#     control(input_df, verbose=True, verbose_columns=['noindiv'])
#     control(df_foy, verbose=True, verbose_columns=['noindiv'])
    
#     print input_df.duplicated('noindiv').sum(), len(input_df)
#     print df_foy.duplicated('noindiv').sum(), len(df_foy)
#     print df_fam.duplicated('noindiv').sum(), len(df_fam)
#     print df_men.duplicated('noindiv').sum(), len(df_men)
#     print df_ind.head(10).to_string()
    print '    FAM'
    print df_fam['noi'].head(10).to_string()
    print '    FOY'
    print df_foy['noi'].head(10).to_string()
    print '    MEN'
    print df_men['noi'].head(10).to_string()

#     print df_fam.columns
    print '    INPUT'
    print input_df['noi'].head(10).to_string()
#     print input_df.loc[input_df.duplicated('noindiv'), ['noindiv', 'idfoy']].head(10).to_string()
#     output['survey_2006/fam'] = df_fam.drop_duplicates('idfam')


def survey_case_3_tables():
    year = 2006 
    yr = str(year)
    simulation = SurveySimulation()
    
    
    survey_input = HDFStore(survey3_test)
#     convert_to_3_tables(year=year, survey_file=survey_file, output_file=survey3_file)
    df_men = survey_input['survey_2006/men']
    df_foy = survey_input['survey_2006/foy']
    df_fam = survey_input['survey_2006/fam']
    df_fam['alr'] = 0;
    survey_input['survey_2006/fam'] = df_fam
      
    simulation.num_table = 3

    simulation.set_config(year = yr, country = country, survey_filename=survey3_test)
    simulation.set_param()
 
    simulation.compute()
     
# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()
     
    df1 = agg.aggr_frame
    print df1.to_string()
     
# #    Saving aggregates
#     if writer is None:
#         writer = ExcelWriter(str(fname)
#     agg.aggr_frame.to_excel(writer, yr, index= False, header= True)
 
 
# Displaying a pivot table    
    from src.plugins.survey.distribution import OpenfiscaPivotTable
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df2 = pivot_table.get_table(by ='so', vars=['nivvie']) 
    print df2.to_string()

if __name__ == '__main__':
#     test_convert_to_3_tables()
#     check_converted()
#     test_case_3_tables()
    survey_case_3_tables()
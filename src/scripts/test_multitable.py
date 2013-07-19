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
from pandas import HDFStore
import os
import numpy as np
from src.scripts.data_management.separate_tables_generator import convert_to_3_tables
import pandas as pd
from src import SRC_PATH
from src.countries.france.data.erf.build_survey.utilitaries import check_structure, control
from src.countries.france.data.erf.datatable import DataCollection


country = 'france'

#Setting the files path:
survey_test = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
survey_bis = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test_bis.h5')
survey3_test = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')
survey_file = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey.h5')
survey3_file = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey3.h5')


def test_convert_to_3_tables(year=2006):
    
    #Performing the separation :
    test_hdf = HDFStore(survey_test)
    test_remove_me = test_hdf['survey_2006']
    test_remove_me = test_remove_me.drop_duplicates(['idfoy', 'quifoy'])
    test_bis = HDFStore(survey_bis)
    test_bis['survey_2006'] = test_remove_me
    
    
    convert_to_3_tables(year=year, survey_file=survey_bis, output_file=survey3_test)
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
    
    year = 2006
    erf = DataCollection(year=year)
    df = erf.get_of_values(table = "erf_indivi")
    df2 = erf.get_of_values(table = "eec_indivi")
    print '\n'
    print df.loc[df.ident==6030189, :].to_string()
    print df2.loc[df2.ident==6030189, :].to_string()    

    print len(np.unique(input_df['idfoy'].values))
    print len(np.unique(input_df.loc[input_df['quifoy']==0,'idfoy'].values))
    
    liste = [601228002, 602671302, 602016402, 603069602, 601365902, 602679402, 602680905, 603074902, 600848302, 
             602684902, 601508802, 601427302, 601774602, 600466102, 603448202, 603091202, 602437502, 603224003, 
             603093102, 601261802, 601000002, 601789602, 601660602, 600350102, 601927802, 601797902, 601667902, 
             601537502, 600227602, 602854502, 602071902, 600144702, 602205702, 600769302, 601096602, 602609202, 
             601301302, 602220302, 602486102, 601376802, 601570902, 600654802, 601443202, 603412402, 603412902, 
             601055502, 602893001, 601189902, 601850602, 600539902, 602507002, 601460902, 602511602, 601200902, 
             601601802, 600946903, 600428502, 600953502, 601084802, 601350102, 600829602, 600174402]
    liste_men = np.unique(input_df.loc[input_df.idfoy.isin(liste), 'idmen'].values)
    print liste_men
    print df.loc[df.ident.isin(liste_men), ['noi', 'noindiv', 'ident', 'declar1', 'declar2', 'persfip', 'persfipd', 'quelfic']].head(30).to_string()
    print input_df.loc[input_df.idfoy.isin(liste), :].head(30).to_string()
    
#     print input_df.loc[input_df.idfoy==603018901, 
#                        ['idfoy', 'quifoy', 'idfam', 'quifam', 'idmen', 'quimen', 'noi']].to_string()
#                        
#     print input_df.loc[input_df.idfam==603018902, 
#                    ['idfoy', 'quifoy', 'idfam', 'quifam', 'idmen', 'quimen', 'noi']].to_string()
    return
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
    print sorted(df_fam.columns)
    print '    FOY'
    print sorted(df_foy.columns)
    print '    MEN'
    print sorted(df_men.columns)
    print '    IND'
    print sorted(df_ind.columns)

#     print df_fam.columns
    print '    INPUT'
    print sorted(input_df.columns)
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
    survey_case_3_tables()
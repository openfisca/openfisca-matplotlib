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
from src.scripts.data_management.separate_tables_generator import convert_to_3_tables
import pandas as pd
from src import SRC_PATH
from src.countries.france.data.erf.build_survey.utilitaries import check_structure, control



country = 'france'
#Setting the files path:
survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
filename3 = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')


def test_convert_to_3_tables(year=2006):
    
    #Performing the separation :
    convert_to_3_tables(year=year, survey_file=survey_filename, output_file=filename3)
    import gc
    gc.collect()
    
def check_converted():
    #Retrieving the input and output files for analysis : 
    store = HDFStore(survey_filename)
    input_df = store['survey_2006']
    
    output = HDFStore(filename3)
    
    df_fam = output['survey_2006/fam']
    df_foy = output['survey_2006/foy']
    df_men = output['survey_2006/men']
    df_ind = output['survey_2006/ind']
     
    df_foy['noindiv'] = df_foy['noi'] ; del df_foy['noi']
    df_fam['noindiv'] = df_fam['noi'] ; del df_fam['noi']
    df_men['noindiv'] = df_men['noi'] ; del df_men['noi']
#     print df_fam, df_foy, df_men

#     check_structure(store['survey_2006'])
#     control(input_df, verbose=True, verbose_columns=['noindiv'])
#     control(df_foy, verbose=True, verbose_columns=['noindiv'])
    
    print input_df.duplicated('noindiv').sum(), len(input_df)
    print df_foy.duplicated('noindiv').sum(), len(df_foy)
    print df_fam.duplicated('noindiv').sum(), len(df_fam)
    print df_men.duplicated('noindiv').sum(), len(df_men)
#     print df_ind.head(10).to_string()
    print '    FAM'
    print df_fam['idfam'].head(5).to_string()
    print '    FOY'
    print df_foy['idfoy'].head(5).to_string()
    print '    MEN'
    print df_men['idmen'].head(5).to_string()

#     print df_fam.columns
    print '    INPUT'
    print input_df['noindiv'].head(10).to_string()
#     print input_df.loc[input_df.duplicated('noindiv'), ['noindiv', 'idfoy']].head(10).to_string()
    del input_df


if __name__ == '__main__':
    test_convert_to_3_tables()
#     check_converted()
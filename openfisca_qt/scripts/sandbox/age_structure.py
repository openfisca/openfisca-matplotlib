# -*- coding:utf-8 -*-
# Created on 27 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)



from pandas import ExcelFile, HDFStore
from src.lib.simulation import SurveySimulation
from src.plugins.survey.distribution import OpenfiscaPivotTable
from src.lib.utils import of_import
import os

H5_FILENAME = "age_structure.h5"


def get_age_structure(simulation):
    
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df = pivot_table.get_table(entity = 'ind', by = "age", vars = [])
    return df


def get_agem_structure(simulation):
    
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df = pivot_table.get_table(entity = 'ind', by = "agem", vars = [])
    return df

def build_from_openfisca( directory = None):
    
    df_age_final = None
    for yr in range(2006,2010):
        country = 'france'

        simulation = SurveySimulation()
        simulation.set_config(year = yr, country = country)
        simulation.set_param()
        simulation.set_survey()
        
        
        df_age = get_age_structure(simulation)
        df_age[yr] = df_age['wprm']
        del df_age['wprm']
        if df_age_final is None:
            df_age_final = df_age
        else:  
            df_age_final = df_age_final.merge(df_age)
        
    if directory is None:
        directory = os.path.dirname(__file__)

    fname = os.path.join(directory, H5_FILENAME)
    store = HDFStore(fname)
    print df_age_final.dtypes
    store.put("openfisca", df_age_final)
    store.close()


#    fname = os.path.join(directory, 'age_structure.xlsx')
#    writer = ExcelWriter(fname)
#    df_age_final.to_excel(writer, sheet_name="age", float_format="%.2f")
#    writer.save()

def build_from_insee( directory = None, verbose=False):
    
    if directory is None:
        directory = os.path.dirname(__file__)

    fname = os.path.join(directory, H5_FILENAME)
    store = HDFStore(fname)
    DATA_SOURCES_DIR = of_import("","DATA_SOURCES_DIR","france")
    xls = ExcelFile(os.path.join(DATA_SOURCES_DIR, "sd2010_t6_fm.xls"))
    
    df_age_final = None
    
    for year in range(2006,2010):
        sheet_name = str(year)
    
        df = xls.parse(sheet_name, header=0, index_col=0, skiprows=8, parse_cols=[1,2], na_values=['NA'])
    
        df.index.name = u"âge"
        df.rename(columns = {"Unnamed: 1" : year}, inplace = True)     
        
        # Dealing with te 90 et plus and 105 et plus
        df = df.reset_index()
        df = df.dropna(axis=0)    
        df.set_value(106,u"âge", 105)
        df = df.set_index(u"âge")
        df = df.drop(df.index[90], axis=0)
        df.index.name = u"âge"
        df = df.reset_index()
        if verbose:
            print "year : " + str(year) 
            print df.to_string()
    
    
        if df_age_final is None:
            df_age_final = df
        else:  
            df_age_final = df_age_final.merge(df)
        
    if verbose:
        print df_age_final.to_string()
        print df_age_final.dtypes
    
    from numpy import dtype 
    df_age_final[u"âge"] = df_age_final[u"âge"].astype(dtype("int64"))    
    store.put("insee", df_age_final)


def build_all():
    build_from_insee()
    build_from_openfisca()


def build_comparison():
    directory = os.path.dirname(__file__)    
    fname = os.path.join(directory, H5_FILENAME)
    store = HDFStore(fname)

    openfisca = store.get("openfisca")
    insee = store.get("insee")
    print openfisca
    print insee
#    for year in range(2006,2010):
    print openfisca.head()
    openfisca = openfisca.drop(0, axis=0)
    openfisca.reset_index(inplace=True)
    from pandas import DataFrame
    print (openfisca.sum() - insee.sum())/insee.sum()

    df = (openfisca-insee)/insee
    print df
    print df.to_string()
        
def test():

    directory = os.path.dirname(__file__)    
    fname = os.path.join(directory, H5_FILENAME)
    store = HDFStore(fname)
    print store
    print store.keys()
    
    
if __name__ == '__main__':
#    build_from_insee()
    build_comparison()
#    test()
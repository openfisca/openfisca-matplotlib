# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Script to compute the aggregates for all the referenced years

from src.lib.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates
from pandas import ExcelWriter, ExcelFile
import os

country = 'france'
destination_dir = "c:/users/utilisateur/documents/"
fname_all = "aggregates_inflated_loyers.xlsx"
fname_all = os.path.join(destination_dir, fname_all)              


def get_loyer_inflator(year):
    
    xls = ExcelFile('../countries/france/data/sources/loyers.xlsx')
    df = xls.parse('data', na_values=['NA'])   
    irl_2006 = df[ (df['year'] == 2006) & (df['quarter'] == 1)]['irl']
#    print irl_2006
    irl = df[ (df['year'] == year) & (df['quarter'] == 1)]['irl']
#    print irl 
    return float(irl.values/irl_2006.values)

def build_aggregates():

    writer = None
    years = range(2006,2010)
    for year in years:        
        yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
        inflator = get_loyer_inflator(year)
        simu.inflate_survey({'loyer' : inflator})
        simu.compute()
        
        agg = Aggregates()
        agg.set_simulation(simu)
        agg.compute()

        if writer is None:
            writer = ExcelWriter(str(fname_all))
        agg.aggr_frame.to_excel(writer, yr, index= False, header= True)
        del simu
        del agg
        import gc
        gc.collect()
    
    writer.save()


def diag_aggregates():
    
    years = ['2006', '2007', '2008', '2009']
    
    df_final = None
    for yr in years:
        xls = ExcelFile(fname_all)
        df = xls.parse(yr, hindex_col= True)
        
        cols = [u"Mesure",
                u"Dépense \n(millions d'€)", 
                u"Bénéficiaires \n(milliers)", 
                u"Dépenses \nréelles \n(millions d'€)", 
                u"Bénéficiaires \nréels \n(milliers)", 
                u"Diff. relative \nDépenses",
                u"Diff. relative \nBénéficiaires"]
        selected_cols = [u"Mesure", u"Diff. relative \nDépenses", u"Diff. relative \nBénéficiaires"]
        df = df[selected_cols]
        df['year'] = yr
        df['num'] = range(len(df.index))
        df = df.set_index(['num', u'Mesure', 'year'])
        if df_final is None:
            df_final = df
        else:  

            df_final = df_final.append(df, ignore_index=False)
    
#    DataFrame.groupby()
    df_final = df_final.sortlevel(0)
    print str(fname_all)[:-5]+'_diag.xlsx'
    writer = ExcelWriter(str(fname_all)[:-5]+'_diag.xlsx')
    df_final.to_excel(writer, sheet_name="diagnostics", float_format="%.2f")
    writer.save()


def build_erf_aggregates():
    DATA_DIR = 'C:/Users/Utilisateur/Documents/Data/'
#    from src.lib.utils import of_import
#    DATA_DIR = DATA_DIR
#    R_USER = os.getenv("R_USER")
#    if R_USER is None:
#        import win32api
#        R_USER = win32api.GetUserName()
#
#    os.environ['R_USER'] = R_USER    
    import pandas.rpy.common as com 
    import rpy2.rpy_classic as rpy
    rpy.set_default_mode(rpy.NO_CONVERSION)

    for year in range(2006,2010):
        menageXX = "menage" + str(year)[2:]
        menageRdata = menageXX + ".Rdata"
        filename = os.path.join(os.path.dirname(DATA_DIR),'R','erf', str(year), menageRdata)
        yr = str(year)
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
    
        agg = Aggregates()
        agg.set_simulation(simu)
        # print agg.varlist
        rpy.r.load(filename)

        menage = com.load_data(menageXX)
        cols = []
        print year
        for col in agg.varlist:
            #print col
            erf_var = "m_" + col + "m" 
            if erf_var in menage.columns:
                cols += [erf_var] 

        df = menage[cols]
        wprm = menage["wprm"]
        for col in df.columns:
            
            tot = (df[col]*wprm).sum()/1e9
            print col, tot
    
    


if __name__ == '__main__':


#    build_aggregates()
#    diag_aggregates()
#    test()

    build_erf_aggregates()
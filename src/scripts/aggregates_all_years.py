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

from src.plugins.survey.distribution import OpenfiscaPivotTable

def get_age_structure(simulation):
    
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df = pivot_table.get_table(entity = 'ind', by = "age", vars = [])
    return df


from pandas import DataFrame

def test():
    for yr in range(2006,2010):
        country = 'france'
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
        df = get_age_structure(simu)


def test2():
        yr = 2008
        country = 'france'
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
        df = get_age_structure(simu)
    
        print df.to_string()
        df = DataFrame({'x' : simu.survey.get_value("wprm", simu.survey.index['men'], sum_=True)})

        print df.describe()

        df2 = DataFrame({'y' : simu.survey.get_value("wprm", simu.survey.index['ind'], sum_=False)})
        print df2.describe()

        df3 = DataFrame({'z' : simu.survey.get_value("idmen", simu.survey.index['men'], sum_=True)})
        df4 = DataFrame({'t' : simu.survey.get_value("noi", simu.survey.index['ind'])})
        
        print (df3.z==0).sum()
        print (df4.t==1).describe()

if __name__ == '__main__':


#    build_aggregates()
#    diag_aggregates()
    test()
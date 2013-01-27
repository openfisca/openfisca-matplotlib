# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Script to compute the aggregates for all the referenced years

from src.core.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates
from pandas import ExcelWriter, ExcelFile
import os

country = 'france'
destination_dir = "c:/users/utilisateur/documents/"
fname_all = "aggregates.xlsx"
fname_all = os.path.join(destination_dir, fname_all)              


def build_aggregates():

    writer = None
    years = ['2006', '2007', '2008', '2009']
    for yr in years:

#        fname = "Agg_%s.%s" %(str(yr), "xls")
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
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


if __name__ == '__main__':


    #build_aggregates()
    diag_aggregates()
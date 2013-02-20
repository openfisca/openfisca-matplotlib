# -*- coding:utf-8 -*-
'''
Created on 20 févr. 2013

@author: benjello
'''

from src.lib.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates
#from pandas import ExcelWriter, ExcelFile
import os

country = 'france'
destination_dir = "c:/users/utilisateur/documents/"
fname_all = "aggregates_euromod.xlsx"
fname_all = os.path.join(destination_dir, fname_all)              


def build_aggregates():
#    writer = None
    years = range(2006,2007)
    for year in years:        
        yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()       
        simu.compute()
        var_list = ["ci_garext", "inthab", "abat_rnps", "ppe_tot", "rni"]
        simu.aggregated_by_entity("men", var_list)
        agg = Aggregates()
        agg.set_simulation(simu)
        agg.set_var_list(var_list)
        agg.compute()
        agg.aggr_frame.to_string()
#        if writer is None:
#            writer = ExcelWriter(str(fname_all))
#        agg.aggr_frame.to_excel(writer, yr, index= False, header= True)
#        del simu
#        del agg
#        import gc
#        gc.collect()
    
#    writer.save()


if __name__ == '__main__':
    build_aggregates()





#- Les déductions pour les revenus des valeurs et capitaux mobiliers (section 2 de la déclaration des revenus)
# 
#Il s’agit des deductions fiscales de la variable _ rev_cat_rvcm
# 
#- Les déductions pour les revenus fonciers (section3)
# 
#Il s’agit des deductions fiscales de la variable _rev_cat_rfon
 

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
from src.plugins.survey.inequality import Inequality
from pandas import ExcelWriter, ExcelFile, HDFStore
import os

import pandas.rpy.common as com
import pdb

country = 'france'

from src.countries.france.data.sources.config import destination_dir


fname_all = "aggregates_inflated_loyers.xlsx"
fname_all = os.path.join(destination_dir, fname_all)              
num_output = None


def compar_num_table():

    writer = None
    years = range(2006,2007)
    tot1 = 0 
    tot3 = 0
    filename = destination_dir+'output3.h5'
    store = HDFStore(filename)
    for year in years:        
        yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        import time
        
        
        deb3 = time.clock()
        sous_ech =  [6000080, 6000080, 6000195, 6000195, 6000288, 6000288, 6000499, 6000499, 6000531, 6000531, 6000542, 6000542]
        sous_ech =  [6000191, 6000191, 6000531, 6000614, 6000195, 6000195, 6000499, 6000499, 6000531, 6000614, 6000531, 
        6000614, 6000531, 6000531, 6000195, 6000195, 6000288, 6000288, 6000499, 6000499, 6000531, 6000542,
         6000542, 6000614, 6000191]
        
        #al
        sous_ech =  [6000122, 6000865, 6001256]
        # typ_men
        sous_ech =  [6006630, 6006753, 6008508]
        # foy
        sous_ech =  [6036028, 6028397, 6019248]
            
        sous_ech = None
        simu.set_survey(num_table=3, subset=sous_ech)
        simu.compute()
 
        agg3 = Aggregates()
        for ent in ['ind','men','foy','fam']:
            tab = simu.output_table.table3[ent]
            renam={}
            renam['wprm_'+ent] = 'wprm'
            tab = tab.rename(columns=renam)
        agg3.set_simulation(simu)
        agg3.compute()       
        
        fin3  = time.clock()
        

#        if writer is None:
#            writer = ExcelWriter(str(fname_all))  
        fname_all = os.path.join(destination_dir, 'agg3.xlsx') 
        agg3.aggr_frame.to_excel(fname_all, yr, index= False, header= True)



        # export to csv to run compar in R
        for ent in ['ind','men','foy','fam']:
            dir_name = destination_dir + ent +'.csv'
            tab = simu.output_table.table3[ent]
            renam ={}
            renam['wprm_'+ent] = 'wprm'
            if ent=='ind':
                ident = ["idmen","quimen","idfam","quifam","idfoy","quifoy"]
            else:
                ident = ["idmen","idfam","idfoy"]
            for nom in ident:
                renam[nom+'_'+ent] = nom
            tab = tab.rename(columns=renam)
            order_var = ident+list(tab.columns - ident)
            tab.sort(['idmen','idfam','idfoy']).ix[:num_output,order_var].to_csv(dir_name)

        
        deb1 = time.clock()
        simu.set_survey(num_table=1, subset=sous_ech)
        simu.compute()
        
        agg = Aggregates()
        agg.set_simulation(simu)
        agg.compute()
                
        fin1  = time.clock()        
        
        # export to csv to run compar in R
        dir_name = destination_dir + 'en1' +'.csv'
        tab = simu.output_table.table
        tab = tab.drop(['idfam_fam','idfam_foy','idfam_men','idfoy_fam','idfoy_foy','idfoy_men','idmen_men','idmen_fam','idmen_foy','wprm_foy','wprm_fam'],axis=1)
        renam ={}
        ent = 'ind'
        renam['wprm_'+ent] = 'wprm'
        ident = ["noi","idmen","quimen","idfam","quifam","idfoy","quifoy"]
        for nom in ident:
            renam[nom+'_'+ent] = nom  
        tab = tab.rename(columns=renam)
        order_var = ident+list(tab.columns - ident)   
        tab.sort(['idmen','idfam','idfoy']).ix[:num_output,order_var].to_csv(dir_name)


#        if writer is None:
#            writer = ExcelWriter(str(fname_all))
        fname_all = os.path.join(destination_dir, 'agg1.xlsx') 
        agg.aggr_frame.to_excel(fname_all, yr, index= False, header= True)
        del simu
        del agg
        import gc
        gc.collect()
        tot1 += fin1 - deb1
        tot3 += fin3 - deb3
        print "Time to process 1 table :" +str(fin1 - deb1)
        print "Time to process 3 table :" +str(fin3 - deb3)
    print tot1, tot3, tot3- tot1

if __name__ == '__main__':

    compar_num_table()


# -*- coding:utf-8 -*-
# Created on 16 avr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from src.lib.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates
from src.plugins.survey.aggregates3 import Aggregates3
from pandas import ExcelWriter, ExcelFile
import os

from src.countries.france.data.sources.config import destination_dir
country = 'france'


num_output = 100

def build_aggregates3():

    writer = None
    years = range(2006,2007)
    tot1 = 0 
    tot3 = 0
    for year in years:        
        yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        import time
        
        
        deb3 = time.clock()
        simu.set_survey(num_table=3)
        simu.compute()
        fin3  = time.clock()
        
        print "coucou"
        col = simu.survey.description.get_col("so")
        print col.entity
        agg3 = Aggregates3()
        agg3.set_simulation(simu)
        agg3.compute()
#        if writer is None:
#            writer = ExcelWriter(str(fname_all))  
        fname_all = os.path.join(destination_dir, 'agg3.xlsx') 
        agg3.aggr_frame.to_excel(fname_all, yr, index= False, header= True)

        for ent in ['ind','men','foy','fam']:
            dir_name = destination_dir + ent +'.csv'
##            simu.survey.table3[ent].to_csv(dir_name)
#            import pdb
#            pdb.set_trace()
##            com.convert_to_r_dataframe
            simu.outputs.table3[ent][:num_output].to_csv(dir_name)

        
        deb1 = time.clock()
        simu.set_survey(num_table=1)
        print "prob compute"
        simu.compute()
        fin1  = time.clock()        
        
        dir_name = destination_dir + 'en1' +'.csv'
        print "prob output"
        simu.outputs.table[:num_output].to_csv(dir_name)
        
        agg = Aggregates()
        print "prob set"
        agg.set_simulation(simu)
        print "prob compute"
        agg.compute()

#        if writer is None:
#            writer = ExcelWriter(str(fname_all))
        fname_all = os.path.join(destination_dir, 'agg1.xlsx') 
        print "prob ind"
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
#    writer.save()


if __name__ == '__main__':

    build_aggregates3()
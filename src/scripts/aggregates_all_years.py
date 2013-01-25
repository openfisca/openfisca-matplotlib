# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Script to compute the aggregates for all the referenced years

from src.core.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates, ExcelWriter
import os



if __name__ == '__main__':


    writer = None
    years = ['2006', '2007', '2008', '2009']
    for yr in years:
        country = 'france'
        destination_dir = "c:/users/utilisateur/documents/"
        fname = "Agg_%s.%s" %(str(yr), "xls")

        fname_all = "aggregates.xlsx"
        fname_all = os.path.join(destination_dir, fname_all)               
        
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
        simu.compute()
        
        agg = Aggregates()
        agg.set_simulation(simu)
        agg.compute()
#        agg.save_table(directory = destination_dir, filename = fname)
 
        print agg.aggr_frame
        break
        if writer is None:
            writer = ExcelWriter(str(fname_all))
        agg.aggr_frame.to_excel(writer, yr, index= False, header= True)
        del simu
        del agg
        import gc
        gc.collect()
    
    
    #writer.save()


    
# -*- coding:utf-8 -*-
"""
Created on Nov 30, 2012
@author: Mahd Ben Jelloul

openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""


from core.simulation import SurveySimulation 
from src.plugins.survey.aggregates import Aggregates

if __name__ == '__main__':


    yr = 2009
    country = 'france'
    destination_dir = "c:/users/utilisateur/documents/"
    
    fname = "Avtg_Enf_Agg_%s.%s" %(str(yr), "xls")
    simu = SurveySimulation()
    simu.set_config(year = yr, country = country)
    simu.set_param()
    
    simu.set_survey()
    simu.compute()
    
    agg = Aggregates()
    agg.set_simulation(simu)
    agg.compute()
    agg.save_table(directory = destination_dir, filename = fname)
    del simu
    del agg
    import gc
    gc.collect()

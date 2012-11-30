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
from src.core.simulation import SurveySimulation 

if __name__ == '__main__':

    #years = ['2006', '2007', '2008', '2009']
    #for yr in years:
        
    yr = 2006
    country = 'france'

    simu = SurveySimulation()
    simu.set_config( year = yr, country = country)
    simu.initialize()
    simu.set_survey()
    res = simu.compute()
    print res
    
    
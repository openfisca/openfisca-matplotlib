# -*- coding:utf-8 -*-
"""
Created on Dec 6, 2012
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


from core.simulation import ScenarioSimulation 

import sys
from PyQt4.QtGui import QMainWindow, QApplication
from src.widgets.matplotlibwidget import MatplotlibWidget

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self, title='Example')
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        

from datetime import datetime    



if __name__ == '__main__':

    


    yr = 2006
    country = 'france'
    destination_dir = "c:/users/utilisateur/documents/"
    
    fname = "Agg_%s.%s" %(str(yr), "xls")
    simu = ScenarioSimulation()
    simu.set_config(year = yr, country = country, nmen = 201, xaxis = 'sal', maxrev = 100000, reforme = False, mode ='bareme')
    simu.set_param()
    simu.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part')
    simu.scenario.addIndiv(2, datetime(2000,1,1).date(), 'pac', 'enf')
    simu.scenario.addIndiv(3, datetime(2000,1,1).date(), 'pac', 'enf')
    simu.set_marginal_alternative_scenario()
    simu.alternative_scenario.addIndiv(4, datetime(2000,1,1).date(), 'pac', 'enf')
    
    print simu.scenario
    print simu.alternative_scenario
    df =  simu.get_results_dataframe()
    print df.columns
    print df.to_string()
#    

    app = QApplication(sys.argv)
    win = ApplicationWindow()
    
    ax = win.mplwidget.axes
     
    simu.draw_bareme(ax) 
    win.mplwidget.draw()

    win.show()
    sys.exit(app.exec_())    

        
        
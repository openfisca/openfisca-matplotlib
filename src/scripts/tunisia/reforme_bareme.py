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



from src.lib.simulation import ScenarioSimulation 

import sys
from src.gui.qt.QtGui import QMainWindow, QApplication

from src.widgets.matplotlibwidget import MatplotlibWidget

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        

from datetime import datetime    

destination_dir = "c:/users/utilisateur/documents/tunisie/"    

if __name__ == '__main__':


    app = QApplication(sys.argv)
    win = ApplicationWindow()    

    country = 'tunisia'
    yr = 2011
    win = ApplicationWindow()
    ax = win.mplwidget.axes    
    simulation = ScenarioSimulation()        
    simulation.set_config(year = yr, country = country, nmen = 11, 
                    xaxis = 'sali', maxrev = 10000, reforme = False,
                    mode ='bareme', same_rev_couple = False)
    simulation.set_param()
    simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
    
    simulation.draw_bareme(ax, legend = True, position = 4) 
    win.resize(1400,700)
    win.mplwidget.draw()
    win.show()

    df = simulation.get_results_dataframe()
    print df.to_string()

    
#    win.mplwidget.print_figure(destination_dir + title + '.png')
    del ax, simulation 
    sys.exit(app.exec_())




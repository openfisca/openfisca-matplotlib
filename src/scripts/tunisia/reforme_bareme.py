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
import os
from src.gui.qt.QtGui import QMainWindow, QApplication

from src.widgets.matplotlibwidget import MatplotlibWidget
from datetime import datetime    

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        
def run_simulation(year=2011, apply_reform=False, reforme=False):
    country = 'tunisia'
   
    simulation = ScenarioSimulation()        
    simulation.set_config(year = year, country = country, nmen = 1001, 
                    xaxis = 'sali', maxrev = 100000, reforme = reforme,
                    mode ='bareme', same_rev_couple = False)
    simulation.set_param()
#    simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
    if apply_reform:
        simulation.P.ir.reforme.exemption.active = 1
    return simulation

if __name__ == '__main__':

    destination_dir = u"c:/users/utilisateur/Desktop/Tunisie/Réforme barème"
    app = QApplication(sys.argv)
    win = ApplicationWindow()    
    win = ApplicationWindow()
    
    ax = win.mplwidget.axes    
    
    simulation = run_simulation(year=2011, apply_reform=False)
    title = "Actuel" 

#     simulation = run_simulation(year=2011, apply_reform=False)
#     title = "Réforme" 
    
#    simulation = run_simulation(year=2011, apply_reform=True, reforme=True)
#    title = u"Réforme différence" 
    
#    simulation.draw_bareme(ax, legend = True, position = 4) 
    
    simulation.draw_taux(ax, legend=True)
    
    win.resize(1400,700)
    win.mplwidget.draw()
    win.show()

    df = simulation.get_results_dataframe()
    print df.to_string()

    
#    win.mplwidget.print_figure(os.path.join(destination_dir, title + '.png'))

    del ax, simulation 
    sys.exit(app.exec_())




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
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        

from datetime import datetime    



if __name__ == '__main__':


    app = QApplication(sys.argv)
    win = ApplicationWindow()    

    country = 'france'
    destination_dir = "c:/users/utilisateur/documents/"    
    yr = 2010

    marginal = True
    
    for n_enf_final in range(1,5):
        if n_enf_final == 1:
            title = str(n_enf_final) + ' enfant'
            if marginal:
                title = str(n_enf_final) + 'er enfant'
        else:
            title = str(n_enf_final) + ' enfants'
            if marginal:
                title = str(n_enf_final) + 'e enfant'

        win = ApplicationWindow()
        ax = win.mplwidget.axes        
        simu = ScenarioSimulation()
        
        simu.set_config(year = yr, country = country, nmen = 201, xaxis = 'sali', maxrev = 130000, reforme = False, mode ='bareme', same_rev_couple = True)
        simu.set_param()
        simu.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
        
        if marginal is True:
            for i in range(1,n_enf_final):
                print 'adding %s kid(s)' %i
                simu.scenario.addIndiv(1+i, datetime(2000,1,1).date(), 'pac', 'enf')
            
        simu.set_marginal_alternative_scenario()
        for i in range(1,n_enf_final+1):
            if (marginal is False) or (i == n_enf_final):
                print 'adding %s kid(s)' %i
                simu.alternative_scenario.addIndiv(1+i, datetime(2000,1,1).date(), 'pac', 'enf')
        
        
        ax.set_title(title)
        simu.draw_bareme(ax, legend = True, position = 4) 
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()
        
        win.mplwidget.print_figure(destination_dir + title + '.png')
        del ax, simu 
    sys.exit(app.exec_())




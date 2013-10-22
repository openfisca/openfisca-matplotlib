# -*- coding:utf-8 -*-
"""
Created on Oct 22, 2013
@author: Mahd Ben Jelloul
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
        

if __name__ == '__main__':

    SAVE = False
    SHOW = True
    destination_dir = u"c:/users/utilisateur/Desktop/Simula"
    app = QApplication(sys.argv)
    win = ApplicationWindow()    
    win = ApplicationWindow()
    
    ax = win.mplwidget.axes    

    country = 'france'
    year = 2011
    
    simulation = ScenarioSimulation()        
    simulation.set_config(year = year, country = country, nmen = 101, 
                    xaxis = 'sali', maxrev = 50000,
                    mode ='bareme', same_rev_couple = False)
    simulation.set_param()
    
#    simulation.draw_bareme(ax, legend = True, position = 4) 
    simulation.draw_taux(ax, legend=True)
    
    win.resize(1400,700)
    if SHOW:
        win.mplwidget.draw()
        win.show()

    df = simulation.get_results_dataframe()
    print df.to_string()

    title = "test"
    if SAVE:   
        win.mplwidget.print_figure(os.path.join(destination_dir, title + '.png'))

    del ax, simulation 
    sys.exit(app.exec_())


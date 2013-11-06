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

        
def run_simulation(apply_reform=False, reforme=False,
                    conj = False, kids = 0, sal_conj=False, year=2011):

    country = 'tunisia'
    simulation = ScenarioSimulation()        
    simulation.set_config(year = year, country = country, nmen = 11, 
                    xaxis = 'sali', maxrev = 10000, reforme = reforme,
                    mode ='bareme', same_rev_couple = False)
    simulation.set_param()
        
    if sal_conj:
        conj = True
    
    if conj:
        simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'vous', 'part')
        if sal_conj:
            simulation.scenario.indiv[1].update({'sali': simulation.P.cotsoc.gen.smig})
    
        if kids > 0:    
            for n in range(1,kids+1): 
                simulation.scenario.addIndiv(n+1, datetime(2000,1,1).date(), 'pac', 'enf') 

    print simulation.scenario
    if apply_reform:
        simulation.P.ir.reforme.exemption.active = 1

    return simulation


def produce_graph(name="test", apply_reform=False, reforme=False, conj = False, 
                  sal_conj=False, kids = 0, save_figure = False, destination_dir = None,
                  bareme=True, tax_rates=False, year=2011):
    
    app = QApplication(sys.argv)
    win = ApplicationWindow()    
    ax = win.mplwidget.axes
    simulation = run_simulation(year=year, 
                                apply_reform=apply_reform, 
                                reforme=reforme,
                                conj = conj, 
                                sal_conj=sal_conj,
                                kids=kids)
    
    if bareme:
        simulation.draw_bareme(ax, legend = True, position = 4) 
    
    if tax_rates:
        simulation.draw_taux(ax, legend=True)
    
    win.resize(1400,700)
    win.mplwidget.draw()
    win.show()

    df = simulation.get_results_dataframe()
#    print df.to_string()

    if save_figure and destination_dir is not None:
        win.mplwidget.print_figure(os.path.join(destination_dir, name + '.png'))

    del ax, simulation 
#    sys.exit(app.exec_())
    

# 
# def test_case():
# 
#     title = "Actuel" 
# 
# #     simulation = run_simulation(year=2011, apply_reform=False)
# #     title = "Réforme" 
#     
# #    simulation = run_simulation(year=2011, apply_reform=True, reforme=True)
# #    title = u"Réforme différence" 
#     
# 
#     simulation.draw_bareme(ax, legend = True, position = 4) 
#     
# #    simulation.draw_taux(ax, legend=True)
#     
#     win.resize(1400,700)
#     win.mplwidget.draw()
#     win.show()
# 
#     df = simulation.get_results_dataframe()
#     print df.to_string()
# 
#     
# #    win.mplwidget.print_figure(os.path.join(destination_dir, title + '.png'))
# 
#     del ax, simulation 
#     sys.exit(app.exec_())
# 
# 
# 
#     
#     
#     return simulation

if __name__ == '__main__':
    destination_dir = u"c:/users/utilisateur/Desktop/Tunisie/Réforme barème"
    
 
    for conj in [False, True]:
        name = "simulation_adulte"
        if conj:
            for sal_conj in [False, True]:
                for kids in range(0,3):
                    name = name + "_marié_%i_enf" %kids
                    if sal_conj:
                        name = name + "_conj_smig"
                    produce_graph(name=name, conj = conj, 
                                      sal_conj=sal_conj, kids=kids, 
                                      save_figure=True, 
                                      destination_dir = destination_dir)
                    name="simulation_adulte"
        else:
            produce_graph(name=name, kids=0, save_figure=True, 
                          destination_dir = destination_dir)



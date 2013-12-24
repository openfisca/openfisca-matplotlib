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
    simulation.set_config(year = year, country = country, nmen = 1001, 
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
        simulation.P.cotsoc.gen.smig = 320
        simulation.P_default.cotsoc.gen.smig = 320

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

def do_graphs():
    destination_dir = u"c:/users/utilisateur/Desktop/Tunisie/Réforme barème" 
    for conj in [False, True]:
        name = "simulation_adulte_reforme"
        if conj:
            for sal_conj in [False, True]:
                for kids in range(0,3):
                    name = name + "_marié_%i_enf" %kids
                    if sal_conj:
                        name = name + "_conj_smig"
                    produce_graph(name=name, 
                                  conj = conj, 
                                  sal_conj=sal_conj, kids=kids, 
                                  save_figure=True, 
                                  destination_dir = destination_dir,
                                  apply_reform=True,
                                  reforme=True)
                    name="simulation_adulte_reforme"
        else:
            produce_graph(name=name, kids=0, save_figure=True, 
                          destination_dir = destination_dir)





def test_case(year):
    
    country = 'tunisia'
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=False,
                    nmen = 11, maxrev = 12000, xaxis = 'sali')
    # Adding a husband/wife on the same tax sheet (foyer)
    simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
    simulation.scenario.addIndiv(2, datetime(2000,1,1).date(), 'pac', 'enf') 
    simulation.scenario.addIndiv(3, datetime(2000,1,1).date(), 'pac', 'enf')

        
    simulation.set_param()
    simulation.P.ir.reforme.exemption.active = 1

    
    df = simulation.get_results_dataframe()
    print df.to_string()


def justify_decote():
    destination_dir = u"c:/users/utilisateur/Desktop/Tunisie/Réforme barème" 
    produce_graph(name="test2", apply_reform=True, reforme=False, conj = False, 
                  sal_conj=False, kids = 0, save_figure = True, destination_dir = destination_dir,
                  bareme=True, tax_rates=False, year=2011)

if __name__ == '__main__':
    #test_case(2011)
    #do_graphs()
    justify_decote()
    
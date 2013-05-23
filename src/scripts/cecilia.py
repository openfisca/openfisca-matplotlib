# -*- coding:utf-8 -*-
# Created on 17 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

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

SHOW = True
EXPORT = False

def test_case():
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    country = 'france'
    destination_dir = "c:/users/utilisateur/documents/cecilia/"    
    yr = 2010

    simulation = ScenarioSimulation()        
    simulation.set_config(year = yr, country = country, nmen = 1,
                          reforme = False, mode ='castype', decomp_file="decomp_contrib.xml")
    simulation.set_param()
    simulation.get_varying_revenues()
    
    test_case = simulation.scenario  
    
    # Changes in individualized caracteristics    
    #TRAITEMENTS, SALAIRES, PPE, PENSIONS ET RENTES
    # salaires (case 1AJ) 
    test_case.indiv[0].update({"sali":0})
    
    # préretraites, chômage (case 1AP)
    test_case.indiv[0].update({"choi":0})

    # Changes in non-individualized items of the declaration    
    # REVENUS DES VALEURS ET CAPITAUX MOBILIERS
    # intérêts 
    # f2ee intpfl (pdts de placement soumis aux prélèvements obligatoires autres que 2DA et 2DH
    # f2tr intb (intérêts et autres revenus assimilés)
    test_case.declar[0].update({"f2tr":0})
    
    # dividendes
    # f2da divplf (revenus des actions et parts soumis au prélèvement libératoire à 21 %
    # f2dc divb (revenus des actions et parts ouvrant droit à abattement)
    test_case.declar[0].update({"f2dc":0})
    
    # REVENUS FONCIERS
    # foncier  f4ba  (micro foncier f4be)   
    test_case.declar[0].update({"f4ba":20000}) 
    
    
    #PLUS-VALUES DE CESSION DE VALEURS MOBILIERES, DROITS SOCIAUX ET GAINS ASSIMILéS
    # plus-values TODO: F3VG 
    test_case.declar[0].update({"f3vg":0})     
     
     
     
    df = simulation.get_results_dataframe(index_by_code=True)
    rev_cols = ["salsuperbrut", "chobrut", "rstbrut",  "fon", "rev_cap_bar", "rev_cap_lib"]
    prelev_cols = ["cotpat_noncontrib", "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", "cotpat_noncontrib",  
              "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", 
              "csgchod", "csgchoi", "crdscho",
              "csgrstd", "csgrsti", "crdsrst",
              "prelsoc_cap_bar", "prelsoc_cap_lib", "csg_cap_bar", "csg_cap_lib", 
              "crds_cap_bar",  "crds_cap_lib", "imp_lib", "ppe", "irpp" ]

    rev_df = df.loc[rev_cols]
    rev = rev_df.sum(axis=0)
    prelev_df = df.loc[prelev_cols]
    prelev = prelev_df.sum(axis=0)
    
    print -prelev/rev
    ax = win.mplwidget.axes
    if SHOW:
        title ="Mon titre"
        ax.set_title(title)
#        simulation.draw_bareme(ax, legend = True, position = 4) 
        simulation.draw_waterfall(ax) 
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()

    if EXPORT:       
        win.mplwidget.print_figure(destination_dir + title + '.png')
    
    del ax, simulation 
    sys.exit(app.exec_())
    
    
def test_bareme():
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    country = 'france'
    destination_dir = "c:/users/utilisateur/documents/cecilia/"    
    yr = 2010
    simulation = ScenarioSimulation()        
    
    # Changes in individualized caracteristics    
    # salaires: sali

    # retraites: choi

    # intérêts: f2ee intpfl; f2tr intb
        
    # dividendes: f2da divplf; f2dc divb
    
    # foncier  f4ba fon (micro foncier f4be)   
    
    xaxis = "sali"
    maxrev = 300000    
    simulation.set_config(year = yr, country = country, nmen = 101, xaxis = xaxis, maxrev=maxrev,
                          reforme = False, mode ='bareme', decomp_file="decomp_contrib.xml")
    simulation.set_param()
    
    test_case = simulation.scenario  
    
    df = simulation.get_results_dataframe(index_by_code=True)
    rev_cols = ["salsuperbrut", "chobrut", "rstbrut",  "fon", "rev_cap_bar", "rev_cap_lib"]
    prelev_cols = ["cotpat_noncontrib", "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", "cotpat_noncontrib",  
              "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", 
              "csgchod", "csgchoi", "crdscho",
              "csgrstd", "csgrsti", "crdsrst",
              "prelsoc_cap_bar", "prelsoc_cap_lib", "csg_cap_bar", "csg_cap_lib", 
              "crds_cap_bar",  "crds_cap_lib", "imp_lib", "ppe", "irpp"]

    # TODO: vérifier pour la ppe qu'il n'y ait pas de problème
    rev_df = df.loc[rev_cols]
    rev = rev_df.sum(axis=0)
    prelev_df = df.loc[prelev_cols]
    prelev = prelev_df.sum(axis=0)   
    from pandas import DataFrame
    output_df = DataFrame( {"Revenus" : rev, "Prélèvements": prelev, "Taux moyen d'imposition": -prelev/rev}) 
    print output_df.to_string()
    
    ax = win.mplwidget.axes
    if SHOW:
        title ="Mon titre"
        ax.set_title(title)
        graph_xaxis = simulation.get_varying_revenues(xaxis) 
        simulation.draw_bareme(ax, graph_xaxis = graph_xaxis, legend = True, position = 4)
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()

    if EXPORT:       
        win.mplwidget.print_figure(destination_dir + title + '.png')
    
    del ax, simulation 
    sys.exit(app.exec_())
    
    

if __name__ == '__main__':

    test_bareme()
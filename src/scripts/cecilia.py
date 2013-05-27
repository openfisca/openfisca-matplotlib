# -*- coding: windows-1254 -*-
# Created on 17 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from pandas import DataFrame
import sys
import os
from src.gui.qt.QtGui import QMainWindow, QApplication
import matplotlib.pyplot as plt
    
from src.widgets.matplotlibwidget import MatplotlibWidget
from src.lib.simulation import ScenarioSimulation 

SHOW_OPENFISCA = False
EXPORT = False

DESTINATION_DIR = "c:/Users/Laurence Bouvard/Documents/cecilia/"   

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)


def test_case():
    """
    Use to test individual test-case for debugging
    """
    
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    country = 'france'

    yr = 2010

    simulation = ScenarioSimulation()        
    simulation.set_config(year = yr, country = country, nmen = 1,
                          reforme = False, mode ='castype', decomp_file="decomp_contrib.xml")
    simulation.set_param()
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
    test_case.declar[0].update({"f2tr":20000})
    
    # dividendes
    # f2da divplf (revenus des actions et parts soumis au prélèvement libératoire à 21 %
    # f2dc divb (revenus des actions et parts ouvrant droit à abattement)
    test_case.declar[0].update({"f2dc":0})
    
    # REVENUS FONCIERS
    # foncier  f4ba  (micro foncier f4be)   
    test_case.declar[0].update({"f4ba":20000}) 
    
    
    #PLUS-VALUES DE CESSION DE VALEURS MOBILIERES, DROITS SOCIAUX ET GAINS ASSIMILéS
    # plus-values TODO: F3VG et F3VZ 
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
    if SHOW_OPENFISCA:
        title ="Mon titre"
        ax.set_title(title)
        simulation.draw_waterfall(ax) 
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()

    if EXPORT:       
        win.mplwidget.print_figure(DESTINATION_DIR + title + '.png')
    
    del ax, simulation 
    sys.exit(app.exec_())
    
    
def test_bareme():
    """
    Use to test and debug bareme mode test-case
    """
    
    yr = 2010    
    # Changes in individualized characteristics    
    # salaires: sali
    # retraites: choi
    # intérêts: f2ee intpfl; f2tr intb
    # dividendes: f2da divplf; f2dc divb
    # foncier  f4ba fon (micro foncier f4be)

    xaxis = "sali"
    maxrev = 300000    
    year = 2010
    country = 'france'
    simulation = ScenarioSimulation()        
    
    # Changes in individualized caracteristics    
    # salaires: sali
    # retraites: choi
    # intérêts: f2ee intpfl; f2tr intb
    # dividendes: f2da divplf; f2dc divb
    # foncier  f4ba fon (micro foncier f4be)   
    
    simulation.set_config(year = yr, country = country, nmen = 101, xaxis = xaxis, maxrev=maxrev,
                          reforme = False, mode ='bareme', decomp_file="decomp_contrib.xml")
    simulation.set_param()
    test_case = simulation.scenario  
    
    if SHOW_OPENFISCA:
        app = QApplication(sys.argv)
        win = ApplicationWindow()
        ax = win.mplwidget.axes
        title ="Barème openfisca"
        ax.set_title(title)
        graph_xaxis = simulation.get_varying_revenues(xaxis) 
        simulation.draw_bareme(ax, graph_xaxis = graph_xaxis, legend = True, position = 4)
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()
        
    if EXPORT:       
        win.mplwidget.print_figure(DESTINATION_DIR + title + '.png')

    if ax:  
        del ax
    del simulation 
    sys.exit(app.exec_())
    

def get_avg_tax_rate_dataframe(xaxis = "sali", maxrev = 50000, year = 2006):
    """
    Returns avgerage tax rate dataframe
    
    Parameters
    ----------
    
    xaxis : string
            sali choi etc 
    maxrev : float
             Maximal revenu
    year : int, default 2006
           year of the legislation 
    """
    country = 'france'
    simulation = ScenarioSimulation()        
    
    # Changes in individualized caracteristics    
    # salaires: sali
    # retraites: choi
    # intérêts: f2ee intpfl; f2tr intb
    # dividendes: f2da divplf; f2dc divb
    # foncier  f4ba fon (micro foncier f4be)   
    
    simulation.set_config(year = year, country = country, nmen = 101, xaxis = xaxis, maxrev=maxrev,
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

    output_df = DataFrame( {"Revenus" : rev, "Prélèvements": prelev, "Taux moyen d'imposition": -prelev/rev}) 
    output_df.set_index(keys=["Revenus"], inplace=True)
    return output_df


def plot_avg_tax_rate(xaxis="sali", maxrev=50000, year=2006):
    """
    Plot averge tax rate
    
    Parameters
    ----------
    
    xaxis : string, default "sali"
            revenu type
    maxrev : integer, default 50000
             upper bound of the revenu interval
    year : int, default 2006
           year of the legislation
    """
    output_df = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year=year)
    title ="Taux moyens"
    # ax.set_title(title)
    output_df["Taux moyen d'imposition"].plot()
    plt.legend()
    plt.show()


def loop_over_year(xaxis="sali", maxrev=500000, filename=None):
    """
    Plot the average tax rate for a revenue type for every year
    
    Parameters
    ----------
    
    xaxis : string, default "sali"
            revenu type
    maxrev : integer, default 500000
             upper bound of the revenu interval
    filename : path, default None
               if not None, path to save the picture as a pdf
    
    """
    results_df = DataFrame()

    for year in range(2006,2010):
        output_df = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year=year)
        output_df.rename(columns={"Taux moyen d'imposition" : str(year)}, inplace = True) 
        ax = output_df.plot( y=str(year), label=str(year))
        ax.set_xlabel("Revenus")
        
    plt.legend(["Ann�e 2006", "Ann�e 2007", "Ann�e 2008", "Ann�e 2009"],fancybox=True,loc=2)
    plt.title("Taux d'imposition moyen des revenus",color="blue") 
    if filename is not None:
        plt.savefig(filename, format="pdf")
    plt.show()
    


def loop_over_revenue_type(revenues_dict = None):
    """
    Plot the average tax rate for a revenue type for every year
    and every revenue type
    """
    if revenues_dict is None:
        revenues_dict = {"sali" : 300000,
                         "rsti" : 300000,
                         "f2dc" : 300000,
                         "f2tr" : 300000,
                         "f4ba" : 300000,
                         }
        
    for xaxis, maxrev in revenues_dict.iteritems():
        print xaxis
        filename = os.path.join(DESTINATION_DIR,"figure_%s.pdf" %(xaxis))
        loop_over_year(xaxis=xaxis, maxrev=maxrev, filename=filename)


if __name__ == '__main__':
#    test_case()
#    test_bareme()
    
    filename = os.path.join(DESTINATION_DIR,"figure.pdf")
    loop_over_revenue_type()
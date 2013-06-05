# -*- coding:utf-8 -*-
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

SHOW_OPENFISCA = True
EXPORT = False

#DESTINATION_DIR = "c:/Users/Laurence Bouvard/Documents/cecilia/"      
DESTINATION_DIR = "c:/Users/Utilisateur/Documents/cecilia/"      

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)

def complete_2012_param(P):
    # Hack to get rid of missing parameters in 2012
    dummy_simulation = ScenarioSimulation()
    
    dummy_simulation.set_config(year = 2012-1, country = "france", nmen = 1,
                          reforme = False, mode ='castype', decomp_file="decomp_contrib.xml")
    dummy_simulation.set_param()
    
    P.fam = dummy_simulation.P.fam 
    P.minim = dummy_simulation.P.minim
    P.al = dummy_simulation.P.al
    P.ir.crl = dummy_simulation.P.ir.crl
    P.isf = dummy_simulation.P.isf



def test_case(year):
    """
    Use to test individual test-case for debugging
    """
    
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    country = 'france'

    yr = year


    simulation = ScenarioSimulation()        
    simulation.set_config(year = yr, country = country, nmen = 1,
                          reforme = False, mode ='castype', decomp_file="decomp_contrib.xml")
    simulation.set_param()
    
    # Hack to get rid of missing parameters in 2012    
    if yr == 2012:
        complete_2012_param(simulation.P)
     
    test_case = simulation.scenario  
    
    # Changes in individualized caracteristics    
    #TRAITEMENTS, SALAIRES, PPE, PENSIONS ET RENTES
    # salaires (case 1AJ) 
    test_case.indiv[0].update({"sali":0})
    
    # préretraites, chômage (case 1AP)
    test_case.indiv[0].update({"choi":0})

    # pensions (case 1AS)
    test_case.indiv[0].update({"rsti":0})

    # Changes in non-individualized items of the declaration    
    # REVENUS DES VALEURS ET CAPITAUX MOBILIERS
    # intérêts 
    # f2ee intpfl (pdts de placement soumis aux prélèvements obligatoires autres que 2DA et 2DH
    # f2tr intb (intérêts et autres revenus assimilés)
    test_case.declar[0].update({"f2ts":0})
    test_case.declar[0].update({"f2tr":0})
    
    # dividendes
    # f2da divplf (revenus des actions et parts soumis au prélèvement libératoire à 21 %
    # f2dc divb (revenus des actions et parts ouvrant droit à abattement)
    
    test_case.declar[0].update({"f2da":0})
    test_case.declar[0].update({"f2dh":0})
   
    test_case.declar[0].update({"f2dc":0})
    
    # REVENUS FONCIERS
    # foncier  f4ba  (micro foncier f4be)   
    test_case.declar[0].update({"f4ba":0}) 
    
    
    #PLUS-VALUES DE CESSION DE VALEURS MOBILIERES, DROITS SOCIAUX ET GAINS ASSIMILéS
    # plus-values TODO: F3VG 
<<<<<<< HEAD
    test_case.declar[0].update({"f3vg":0})     
    test_case.declar[0].update({"f3vz":0}) 
     
=======
    test_case.declar[0].update({"f3vg":1000000})     
      
      
    test_case.declar[0].update({"f3vz":0})     
    
    
>>>>>>> a0f36ad7cae8f3627a99ddc07610d90a2aeb5f51
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
    print rev
#    print prelev_df, rev, -prelev
    ax = win.mplwidget.axes
    if SHOW_OPENFISCA:
        title ="Mon titre"
        ax.set_title(title)
        simulation.draw_waterfall(ax) 
        win.resize(1400,700)
        win.mplwidget.draw()
        win.show()
        sys.exit(app.exec_())

    if EXPORT:       
        win.mplwidget.print_figure(DESTINATION_DIR + title + '.png')
    
    del ax, simulation 

    
    
def test_bareme(xaxis="sali"):
    """
    Use to test and debug bareme mode test-case
    """
    
    yr = 2012    
    # Changes in individualized characteristics    
    # salaires: sali
    # retraites: choi
    # intérêts: f2ee intpfl; f2tr intb
    # dividendes: f2da divplf; f2dc divb
    # foncier  f4ba fon (micro foncier f4be)


    maxrev = 350000    
    year = 2012
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
    # Hack to get rid of missing parameters in 2012    
    if yr == 2012:
        complete_2012_param(simulation.P)
    
    
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
    
    if year == 2012:
        complete_2012_param(simulation.P)
    
    
    test_case = simulation.scenario  
    df = simulation.get_results_dataframe(index_by_code=True)
    rev_cols = ["salsuperbrut", "chobrut", "rstbrut",  "fon", "rev_cap_bar", "rev_cap_lib", "f3vz", "f3vg"]
    prelev_cols = ["cotpat_noncontrib", "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", "cotpat_noncontrib",  
              "cotsal_noncontrib", "csgsald", "csgsali", "crdssal", 
              "csgchod", "csgchoi", "crdscho",
              "csgrstd", "csgrsti", "crdsrst",
              "prelsoc_cap_bar", "prelsoc_cap_lib", "csg_cap_bar", "csg_cap_lib", 
              "crds_cap_bar",  "crds_cap_lib", "prelsoc_fon", "csg_fon", "crds_fon",
              "prelsoc_pv_immo", "csg_pv_immo", "crds_pv_immo",
              "prelsoc_pv_mo", "csg_pv_mo", "crds_pv_mo",
              "imp_lib", "ppe", "irpp", "ir_pv_immo", ]

    # TODO: vérifier pour la ppe qu'il n'y ait pas de problème
#    print df[100].to_string()
    rev_df = df.loc[rev_cols]
    rev = rev_df.sum(axis=0)
    prelev_df = df.loc[prelev_cols]
    prelev = prelev_df.sum(axis=0)
    avg_rate = -prelev/rev
    
    # Adding IS
    if xaxis in ["f2dc","f2tr"]:
        rate_is = .3443 
        rev_before_is = rev/(1-rate_is)
        prelev = prelev - rate_is*rev_before_is
        avg_rate = (- prelev)/rev_before_is 
        
        rev = rev_before_is

    output_df = DataFrame( {"Revenus" : rev, "Prélèvements": prelev, "Taux moyen d'imposition": avg_rate}) 
    output_df.set_index(keys=["Revenus"], inplace=True)

    xaxis_long_name = simulation.var2label[xaxis]
    return output_df, xaxis_long_name


def plot_avg_tax_rate(xaxis="sali", maxrev=350000, year=2009):
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
    output_df, xaxis_long_name = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year=year)
    title ="Taux moyens"
    # ax.set_title(title)
    output_df["Taux moyen d'imposition"].plot()
    plt.legend()
    plt.show()


def loop_over_year(xaxis="sali", maxrev=350000, filename=None, show=True):
    """
    Plot the average tax rate for a revenue type for every year
    
    Parameters
    ----------
    
    xaxis : string, default "sali"
            revenu type
    maxrev : integer, default 300000
             upper bound of the revenu interval
    filename : path, default None
               if not None, path to save the picture as a pdf
    """
    fig = plt.figure()
    for year in range(2009,2013):
        output_df, xaxis_long_name = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year=year)
        output_df.rename(columns={"Taux moyen d'imposition" : str(year)}, inplace = True) 
        ax = output_df.plot( y=str(year), label=str(year))
        ax.set_xlabel("Revenus")
        ax.set_ylabel("Taux moyen d'imposition")
        
    plt.legend([str(yr) for yr in range(2009,2013)],fancybox=True,loc=2)
    plt.title(xaxis_long_name ,color="blue") 
    if filename is not None:
        plt.savefig(filename, format="pdf")
    if show is False:
        plt.ioff()
    else:
        plt.show()
    plt.close(fig)
    
def loop_over_revenue_type(revenues_dict = None, filename = None, show=True):
    """
    Plot the average tax rate for a revenue type for every year
    and every revenue type
    """
    if revenues_dict is None:
        revenues_dict = {"sali" : 350000,
                         "rsti" : 350000,
                         "f2da" : 350000,
                         "f2dh" : 350000,
                         "f2dc" : 350000,
                         "f2ts" : 350000,
                         "f2tr" : 350000,
                         "f4ba" : 350000,
                         "f3vg" : 350000,
                         "f3vz" : 350000,
                         }
        
    for xaxis, maxrev in revenues_dict.iteritems():
        print xaxis
        if filename is None:
            filename_effective = os.path.join(DESTINATION_DIR,"figure_%s.pdf" %(xaxis))
        else:
            filename_effective = filename
            
        loop_over_year(xaxis=xaxis, maxrev=maxrev, filename=filename_effective, show=show)


def get_target(xaxis = "sali", target = 100000, year = 2010):
    
    def superbrut_rev(maxrev):
        output_df, xaxis_long_name = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year = 2010)
        output_df.reset_index(inplace=True)
        return output_df.iloc[100]["Revenus"] - target
    from scipy.optimize import fsolve

    res  = fsolve(superbrut_rev, target*.6, xtol = 1e-6)
    
    output_df, xaxis_long_name = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=res, year = 2010 )
    return output_df.iloc[100], xaxis_long_name

def loop_over_targets(revenues_dict=None, year=2012):
    if revenues_dict is None:
        revenues_dict = {"sali" : 100000,
                         "rsti" : 100000,
                         "f2dc" : 100000,
                         "f2tr" : 100000,
                         "f4ba" : 100000,
                         }
    for xaxis, target in revenues_dict.iteritems():
        print xaxis    
        output_df, xaxis_long_name = get_target(xaxis=xaxis, target=target, year=year)
        print xaxis_long_name 
        print output_df.reset_index().to_string()
    
def all_in_one_graph(revenues_dict=None, year=2012, filename=None, show=True):
    if revenues_dict is None:
        revenues_dict = {"sali" : 400000,
                         "rsti" : 400000,
                         "f2dc" : 400000,
                         "f2tr" : 400000,
                         "f4ba" : 400000,
                         }

    fig = plt.figure()
    for xaxis, maxrev in revenues_dict.iteritems():
        output_df, xaxis_long_name = get_avg_tax_rate_dataframe(xaxis=xaxis, maxrev=maxrev, year=year)

        ax = output_df.plot( y="Taux moyen d'imposition", label=xaxis_long_name)
        ax.set_xlabel("Revenus")
        ax.set_ylabel("Taux moyen d'imposition")
        
    plt.legend(fancybox=True,loc=4)
    plt.xlim(xmax=300000)
#    plt.title(xaxis_long_name ,color="blue") 
    if filename is not None:
        plt.savefig(filename, format="pdf")
    if show is False:
        plt.ioff()
    else:
        plt.show()
    plt.close(fig)
    
def everything():
    filename = os.path.join(DESTINATION_DIR,"all2012.pdf")
    loop_over_targets()
    all_in_one_graph(filename=filename)
    loop_over_revenue_type(show=False)

if __name__ == '__main__':
<<<<<<< HEAD
    test_case()
#    test_bareme()
#2    plot_avg_tax_rate()         
=======

#    get_target()
#    loop_over_targets()
#    all_in_one_graph()
#    test_case(2011)
#    test_bareme("f3vz")
#    plot_avg_tax_rate("f3vg")         
>>>>>>> a0f36ad7cae8f3627a99ddc07610d90a2aeb5f51
#    filename = os.path.join(DESTINATION_DIR,"figure.pdf")
#    loop_over_year("f2da")
    everything()   

    
    
    

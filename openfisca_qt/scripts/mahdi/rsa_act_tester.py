'''
Created on 9 juil. 2013

@author: benjello
'''


from datetime import datetime
import os

from openfisca_core.simulations import ScenarioSimulation
from openfisca_core.simulations import SurveySimulation
from openfisca_qt.plugins.survey.aggregates import Aggregates
from pandas import ExcelWriter


# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)              


def test_case(year):
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, reforme=False, nmen = 3, maxrev = 1180*12, x_axis = 'sali')
    # Adding a husband/wife on the same tax sheet (foyer)
    simulation.scenario.addIndiv(1, datetime(1975,1,1).date(), 'conj', 'part') 
    simulation.scenario.addIndiv(2, datetime(2000,1,1).date(), 'pac', 'enf')
    simulation.scenario.addIndiv(3, datetime(2000,1,1).date(), 'pac', 'enf')
    simulation.set_param()
    
    # A the aefa prestation can be disabled by uncommenting the following line
    # simulation.disable_prestations( ['aefa'])
    df = simulation.get_results_dataframe()
    print df.to_string()
    
    # Save example to excel
    # destination_dir = "c:/users/utilisateur/documents/"
    # fname = "Example_%s.%s" %(str(yr), "xls")    
    # df.to_excel(destination_dir = "c:/users/utilisateur/documents/" + fname)

def survey_case(year):

    yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
    simulation = SurveySimulation()
    simulation.set_config(year = yr, num_table=1)
    simulation.set_param()

    simulation.compute()
    
    df = simulation.get_variables_dataframe( variables=["rsa_act"], entity='ind')
    print df["rsa_act"].describe()
    
    del simulation
    import gc
    gc.collect()
    return

# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()
    
    df1 = agg.aggr_frame
    print df1.to_string()
    



# Displaying a pivot table    
    from openfisca_qt.plugins.survey.distribution import OpenfiscaPivotTable
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df2 = pivot_table.get_table(by ='so', vars=['nivvie']) 
    print df2.to_string()


if __name__ == '__main__':
    test_case(2010)

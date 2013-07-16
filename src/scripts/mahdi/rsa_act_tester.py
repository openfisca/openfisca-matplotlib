'''
Created on 9 juil. 2013

@author: benjello
'''

from src.lib.simulation import ScenarioSimulation
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from datetime import datetime
from pandas import ExcelWriter
import os


country = 'france'
# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)              



def test_case(year):

    country = 'france'

    simulation = ScenarioSimulation()
    simulation.set_config(year = year, country = country, reforme=False,
                    nmen = 3, maxrev = 1180*12, xaxis = 'sali')
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
    simulation.set_config(year = yr, country = country, num_table=1)
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
    from src.plugins.survey.distribution import OpenfiscaPivotTable
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df2 = pivot_table.get_table(by ='so', vars=['nivvie']) 
    print df2.to_string()


if __name__ == '__main__':
    test_case(2010)
    
        







if __name__ == '__main__':
    pass
'''
Created on 11 juin 2013

@author: Utilisateur
'''
from src.lib.simulation import SurveySimulation

def toto():
    country = "france"
    year = 2006
    
    simulation = SurveySimulation()
    simulation.set_config(country=country, year=year)
    simulation.set_param()
    simulation.set_survey()
    simulation.compute()

    for name in simulation.output_table.description.col_names:
        col =  simulation.output_table.description.get_col(name)
        print col.name
        print col._dtype
        print col.entity
        
#     for name in simulation.output_table._inputs.description.col_names:
#         col =  simulation.output_table._inputs.description.get_col(name)
#         print col.name
#         print col._dtype
#         print col.entity        
    
    

if __name__ == '__main__':
    toto()
    
    
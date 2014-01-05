'''
Created on 11 juin 2013

@author: Utilisateur
'''
from openfisca_core.simulations import SurveySimulation

def toto():
    year = 2006

    simulation = SurveySimulation()
    simulation.set_config(year=year)
    simulation.set_param()
    simulation.set_survey()
    simulation.compute()

    for name, col in simulation.output_table.column_by_name.iteritems():
        print col.name
        print col._dtype
        print col.entity

#     for name, col in simulation.output_table._inputs.column_by_name.iteritems():
#         print col.name
#         print col._dtype
#         print col.entity



if __name__ == '__main__':
    toto()



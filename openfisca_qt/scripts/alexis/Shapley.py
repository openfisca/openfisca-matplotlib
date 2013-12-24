'''
Created on 17 juin 2013
author: Alexis Eidelman
'''


# separer en fonction de la taille du ménage

# pour une taille donnée, faire la liste des possibilité.

def list_permut(n):
    "ABC -> A, AB, AC, BC, ABC"
    subset = [[0],[0,1],[0,2],[1,2],[0,1,2]]
    return subset
    
def define_subset(list):
    
    
    selection = np.zeros(n)
    selection[list] = 1 
    selection.repeat(len(table)/n)
    
    table_bis = table['ind'][selection] # restricted to subset of size n 
    
    # gerer les qui.
     
    # probleme avec le patrimoine   
    table[subset] = simu.output.survey
# -*- coding:utf-8 -*-

"""
Convert a OF individual survey in a three (in fact four)-level survey

@author: alexis Eidelman

"""
from pandas import HDFStore # DataFrame
import numpy as np
import os
import pdb
import src.countries.france.model.data
from src import SRC_PATH
import gc

country = 'france'
filename = None
if filename is None:
    if country is not None:
        filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey.h5')
filename3 = os.path.join(SRC_PATH, 'countries', country, 'data', 'survey3.h5')

store = HDFStore(filename)
output = HDFStore(filename3)

#faire un remove de output pour pouvoir ecraser 
available_years = sorted([int(x[-4:]) for x in  store.keys()])
available_years = [2006]

def getattr_deep(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split('.'), obj)

def from_one_to_three(table,entity):
    from src.lib.utils import of_import
    InputDescription = of_import('model.data', 'InputDescription', country)    
    vars = [x for x in dir(InputDescription()) if x[0] !="_" and x not in ['columns','get_comment','get_title','to_string']]
    vars_entity = []
    for var in vars:  
        if var in table.columns:
            if getattr_deep(InputDescription(), str(var) +'.entity') == entity:
                vars_entity.append(str(var))
    return vars_entity
  

# on peut en profiter pour faire l'index ici ? Ca tournerait un peu plus vite
# mais surtout de maniere plus "essentielle"

for year in available_years: 
    print "debut de l annee %s" %year
    table_in_one = store.select('survey_'+str(year))    
    # delete some people on every table according to test_ident.py results
    print len(table_in_one)
    table_in_one =  table_in_one[ - table_in_one['idfam'].isin([700986003, 700202209, 700150006, 
                                                                700165702, 701609502,
                                                                801132105, 802846205, 800571404,
                                                                901461205,
                                                                800199302, 802008401, 800422201, 802738601,
                                                                903972102, 901676301, 900817401])]
    table_in_one =  table_in_one[ - table_in_one['idmen'].isin([8009658,9046607, 
                                                                8020084, 8001993, 8004222, 8027386,
                                                                9039721, 9047848, 9016763]) ] 
    print len(table_in_one)        
    for entity in ['ind','foy','men','fam']: 
        key = 'survey_'+str(year) + '/'+str(entity)
        vars_entity = from_one_to_three(table_in_one,entity)         
        print entity, vars_entity        
        if entity == 'ind': 
            table_entity = table_in_one[vars_entity]
        # we take care have all ident and selecting qui==0
        else:   
            enum = 'qui'+entity
            table_entity = table_in_one.ix[table_in_one[enum] ==0 ,['noi','idmen','idfoy','idfam'] + vars_entity]
            table_entity= table_entity.rename_axis(table_entity['id'+entity],axis=1)
        print key
        output.put(key, table_entity)
    del table_in_one
    gc.collect()

store.close()
output.close()

# test pour voir si les "lignes" sont nulles
#enum = 'qui'+entity
#table_in_one[enum] == 0
#
#voir = np.array(table_in_one.ix[table_in_one[enum] == 0,vars_entity])
#voir[:,:-1] != 0
#len(np.where( voir[:,:-1] != 0 )[0])
#np.unique(np.where( voir != 0 )[1])


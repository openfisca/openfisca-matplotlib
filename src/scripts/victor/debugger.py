# -*- coding:utf-8 -*-
# Created on 5 juil. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Author: Victor Le Breton

from __future__ import division
from datetime import datetime
import pandas as pd
from pandas import ExcelWriter, HDFStore, DataFrame, merge, Series
import os
import numpy as np
from numpy import logical_and as and_, logical_or as or_
import gc

from src.lib.utils import mark_weighted_percentiles as mwp
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from src.countries.france.data.erf.datatable import DataCollection
from src.lib.datatable import DataTable
from src.lib.columns import Prestation


country= "france"
from src import SRC_PATH

def test(year=2006, variables = ['af']):
    '''
    
    '''
    
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=year, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()
    simulation.compute()

    def get_all_ancestors(varlist):
        if len(varlist) == 0:
            return []
        else:
            if varlist[0]._parents == set():
                return ([varlist[0]]
                      + get_all_ancestors(varlist[1:]))
            else:
                return ([varlist[0]]
                 + get_all_ancestors(list(varlist[0]._parents))
                  + get_all_ancestors(varlist[1:]))
    
    # We want to get all ancestors + children + the options that we're going to encounter
    temp = map(lambda x: simulation.output_table.description.get_col(x), variables)
    temp = get_all_ancestors(temp)
    options = []
    for varcol in temp:
        options.extend(varcol._option.keys())
    options = list(set(options))
    #print options
    temp = map(lambda x: x.name, temp)
    for var in variables:
        temp2 = set()
        varcol = simulation.output_table.description.get_col(var)
        temp2 = temp2.union(set(map(lambda x: x.name, varcol._children)))
    variables = list(set(temp + list(temp2)))
    #print variables
    del temp, temp2
    gc.collect()
    
    def get_var(variable):
        variables =[variable]
        return simulation.aggregated_by_entity(entity="men", variables=variables,  
                                                all_output_vars = False, force_sum=True)[0]
        
    output_df = get_var(variables[0])
    for var in variables[1:]:
        output_df = output_df.merge(get_var(var)[['idmen', var]], on = 'idmen', how = 'outer') 
                                                 
    # We load the data from erf table in case we have to pick data there
    erf_data = DataCollection(year=year)
    os.system('cls')
    todo = set(variables + ["ident", "wprm"]).union(set(options))
    print 'Variables or equivalents to fetch :'
    print todo
    
    '''
    Méthode générale pour aller chercher les variables de l'erf/eec
    ( qui n'ont pas forcément le même nom
    et parfois sont les variables utilisées pour créér l'of ):
    1 - essayer le get_of2erf, ça doit marcher pour les variables principales ( au moins les aggrégats
    que l'on compare )
    Si les variables ne sont pas directement dans la table, 
    elles ont été calculées à partir d'autres variables de données erf/eec 
    donc chercher dans :
    2 - build_survey
    3 - model/model.py qui dira éventuellement dans quel module de model/ chercher
    Le 'print todo' vous indique quelles variables chercher 
    ( attention à ne pas inclure les enfants directs )
    L'utilisation du Ctrl-H est profitable !
    '''
    
    fetch_eec = ['statut','titc','chpub','encadr','prosa','age','naim','naia','ident','noi']
    fetch_erf = ['zsali','af','ident','wprm','noi']
    erf_df = erf_data.get_of_values(variables= fetch_erf, table="erf_indivi")
#     print sorted(erf_df.columns)
#     erf_df['noi'] = 0
    eec_df = erf_data.get_of_values(variables= fetch_eec, table="eec_indivi")
    erf_df_fetched = erf_df.merge(eec_df, on =['ident','noi'], how = 'inner' )
    print erf_df_fetched.columns
    del eec_df

    print 'Loading data from erf_menage table'
    erf_df = erf_data.get_of_values(variables= list(todo), table="erf_menage")
    erf_df['noi'] = 0 # Creation of 'quimen' to ease future merge
     
#     if todo - set(erf_df.columns) != set(): # Need to call upon erf_indivi
#         todo = todo - set(erf_df.columns)
#         print 'Could not get all variables, loading variables from erf_indivi table'
#         temp = erf_data.get_of_values(variables= list(set(list(todo) + ['ident', 'noi'])), table = "erf_indivi")
#         assert 'noi' in temp.columns
#          
#         erf_df = erf_df.merge(temp, on = ['ident','noi'], how = 'right', suffixes = ('(men)', '(ind)'), sort = True)
# #         print erf_df[0:20].to_string()
#         if todo - set(temp.columns) != set():
#             print 'Could not get all variables, loading variables from eec_indivi table'
#             todo = todo - set(temp.columns) 
#             temp = erf_data.get_of_values(variables= list(todo) + ['ident', 'noi'], table = "eec_indivi")
#             erf_df = erf_df.merge(temp, on = ['ident', 'noi'], how = 'inner', suffixes = ('(ind_erf)', '(ind_eec)'), sort = False)
#             if todo - set(erf_df.columns) != set():
#                 print "Warning, couldn't still get all values from erf tables : \n %s \n" %str(todo - set(erf_df.columns))
#         del temp
    del todo
    gc.collect()
    assert 'ident' in erf_df.columns, "ident not in erf_df.columns"
    
#     print sorted(erf_df['ident'])[0:50]
        
    from src.countries.france.data.erf import get_erf2of
    erf2of = get_erf2of()
    erf_df.rename(columns = erf2of, inplace = True)
    
    
# We get the options from the simulation tables:

    # First from the output_table
    s1 = [var for var in set(options).intersection(set(simulation.output_table.table.columns))] + ['idmen_ind', 'quimen_ind']
    output_df_nonaggr = (simulation.output_table.table)[s1]
    output_df_nonaggr.rename(columns = {'idmen_ind' : 'idmen', 'quimen_ind':'quimen'}, inplace = True)
    #print output_df_nonaggr.columns
    #print 'idmen' in output_df_nonaggr.columns
    
    # If not found, we dwelve into the input_table
    if (set(s1)- set(['idmen_ind', 'quimen_ind'])) < set(options):
        s2 = [var for var in (set(options).intersection(set(simulation.input_table.table.columns)) - set(s1))] + ['idmen', 'quimen']
        #print s2
        temp = simulation.input_table.table[s2]
        #print temp.columns
        #print output_df_nonaggr.columns
        output_df_nonaggr = output_df_nonaggr.merge(temp, on = ['idmen', 'quimen'], how = 'inner', sort = False)
        #print 'idmen' in output_df_nonaggr.columns
        
        # Finally, we might add data from erf table
        
        if (set(s1).union(set(s2))- set(['idmen', 'quimen'])) < set(options): # Need to call upon erf table
            print "Warning, some variables couldn't be found in simulation tables"
#             print 'Warning, picking data directly from survey table'
#             s3 = [var for var in set(options).intersection(set(erf_data.get_of_values(variables = None, table ="erf_menage").columns)) - set(s1).union(set(s2))] + ['ident']
#             #print s3
#             temp = erf_data.get_of_values(variables = s3, table = "erf_menage")
#             temp.rename(columns = {'ident' : 'idmen'}, inplace = True)
#             output_df_nonaggr = output_df_nonaggr.merge(temp, on = 'idmen', how = 'inner', sort = False)
#             #print 'idmen' in output_df_nonaggr.columns
#             del s3
            
        del s2, temp
    del s1
    gc.collect()
    
    output_df_nonaggr = output_df_nonaggr[list(set(options)) + ['idmen', 'quimen']]
    #print options, variables
    #print output_df_nonaggr.columns
    assert 'idmen' in output_df_nonaggr.columns, 'Idmen not in output_df_nonaggr columns'
    
#     #print output_df_nonaggr[['idfam_fam', 'idfam_foy', 'idfam_ind', 'idfam_men', 'idfoy_fam', 'idfoy_foy'
#                              , 'idfoy_ind', 'idfoy_men', 'idmen_fam', 'idmen_foy', 'idmen_ind', 'idmen_men']][0:15]

    # Check the idmens that are not common        
    erf_df.rename(columns = {'ident' : 'idmen'}, inplace = True)
    
    print "\n"
    print 'Checking if idmen is here...'
    print '\n ERF : '
    print 'idmen' in erf_df.columns
    print "\n Simulation output"
    print 'idmen' in output_df.columns
    print "\n"

    #print 'Dropping duplicates of idmen for both tables...'
#     assert not erf_df["idmen"].duplicated().any(), "Duplicated idmen in erf_menage" 
    #erf_df.drop_duplicates('idmen', inplace = True)
    output_df.drop_duplicates('idmen', inplace = True)
    assert not output_df["idmen"].duplicated().any(), "Duplicated idmen in of"
    
    print 'Checking mismatching idmen... '
    s1 = set(erf_df['idmen']) - (set(output_df['idmen']))
    if s1:
        print "idmen that aren't in output_df : %s" %str(len(s1))
        pass
    s2 = (set(output_df['idmen'])) - set(erf_df['idmen'])
    if s2:
        print "idmen that aren't in erf_df : %s" %str(len(s2))
        pass
    del s1, s2

    # Restrict to common idmens and merge
    s3 = set(erf_df['idmen']).intersection(set(output_df['idmen']))
    print "Restricting to %s common idmen... \n" %str(len(s3))
    erf_df = erf_df[erf_df['idmen'].isin(s3)]
    output_df = output_df[output_df['idmen'].isin(s3)]
    del s3
    gc.collect()
    
    #print erf_df.columns
    #print output_df.columns
    
    # Compare differences across of and erf dataframes
    print "Comparing differences between dataframes... \n"
    colcom = (set(erf_df.columns).intersection(set(output_df.columns))) - set(['idmen','wprm'])
    print 'Common variables: '
    print colcom
    erf_df.reset_index(inplace = True)
    output_df.reset_index(inplace = True)
    for col in colcom:
        temp = set(erf_df['idmen'][erf_df[col] != output_df[col]])
        print "Numbers of idmen that aren't equal on variable %s : %s \n" %(col, str(len(temp)))
    
    
    # Detect the biggest differences
    bigtable = merge(erf_df, output_df, on = 'idmen', how = 'inner', suffixes=('_erf','_of'))
    print 'Length of new dataframe is %s' %str(len(bigtable))
    #print bigtable.columns
    bigtable.set_index('idmen', drop = False, inplace = True)   
    
    already_met = []
    options_met = []

    for col in colcom:
        bigtemp = None
        table = bigtable[and_(bigtable[col+'_erf']!=0,bigtable[col+'_of']!=0)] 
        table[col] = (table[col+'_erf'] - table[col+'_of']) / table[col+'_erf'] #Difference relative
        table[col] = table[col].apply(lambda x: abs(x))
        print 'Minimum difference between the two tables for %s is %s' %(col, str(table[col].min()))
        print 'Maximum difference between the two tables for %s is %s' %(col, str(table[col].max()))
        print table[col].describe()
        try:
            assert len(table[col]) == len(table['wprm_of']), "PINAGS"
            dec, values = mwp(table[col], np.arange(1,11), table['wprm_of'], 2, return_quantiles=True)
            #print sorted(values)
            dec, values = mwp(table[col], np.arange(1,101), table['wprm_erf'], 2, return_quantiles=True)
            #print sorted(values)[90:]
            del dec, values
            gc.collect()
        except:
            #print 'Weighted percentile method didnt work for %s' %col
            pass
        print "\n"
    
    # Show the relevant information for the most deviant households
        table.sort(columns = col, ascending = False, inplace = True)
        #print table[col][0:10].to_string() #Should #print the idmen along with col by descreasing number of discrapencies
        if bigtemp is None:
            bigtemp = {'table' : table[[col, col+'_of', col+'_erf', 'idmen']][0:10],
                       'options' : None}
        #print "\n"
        
        # If variable is a Prestation, we show the dependancies
        varcol = simulation.output_table.description.get_col(col)
        if isinstance(varcol, Prestation):
            if not varcol._children is None:
                temp = list(varcol._children)
                temp = map(lambda x: x.name, temp)
                temp2 = []
                    
                if set(temp) <= set(output_df.columns):
                    print "Variables which need %s to be computed :\n %s \n" %(col, str(temp))
                    for var in temp:
                        if var + '_of' in table.columns:
                            temp2.append(var + '_of')
                        else:
                            temp2.append(var)
                elif set(temp) <= set(output_df.columns).union(erf_df.columns):
                    print "Variables which need %s to be computed (some missing picked in erf):\n %s \n" %(col, str(temp))
                    for var in temp:
                        if var in output_df.columns:
                            if var + '_of' in table.columns:
                                temp2.append(var + '_of')
                        elif var + '_erf' in table.columns:
                                temp2.append(var + '_erf')
                        else:
                            temp2.append(var)
                else:
                    print "Variables which need %s to be computed (some missing):\n %s \n" %(col, str(temp))
                    for var in temp:
                
                        if var in output_df.columns:
                            if var + '_of' in table.columns:
                                temp2.append(var + '_of')
                        elif var in erf_df.columns:
                            if var + '_erf' in table.columns:
                                temp2.append(var + '_erf')
                                
                print table[[col] + temp2][0:10]
                print "\n"
    
            def iter_on_parents(varcol):
                if (varcol._parents == set() and varcol._option == {}) or varcol.name in already_met:
                    return
                else:
                    temp = list(varcol._parents)
                    temp = map(lambda x: x.name, temp)
                    temp2 = []
                        
                    if set(temp) <= set(output_df.columns):
                        #print "Variables the prestation %s depends of :\n %s \n" %(varcol.name, str(temp))
                        for var in temp:
                            if var + '_of' in table.columns:
                                temp2.append(var + '_of')
                            else:
                                temp2.append(var)
                    elif set(temp) <= set(output_df.columns).union(erf_df.columns):
                        #print "Variables the prestation %s depends of (some missing picked in erf):\n %s \n" %(varcol.name,str(temp))
                        for var in temp:
                            if var in output_df.columns:
                                if var + '_of' in table.columns:
                                    temp2.append(var + '_of')
                            elif var + '_erf' in table.columns:
                                    temp2.append(var + '_erf')
                            else:
                                temp2.append(var)
                    else:
                        for var in temp:
                            if var in output_df.columns:
                                if var + '_of' in table.columns:
                                    temp2.append(var + '_of')
                            elif var in erf_df.columns:
                                if var + '_erf' in table.columns:
                                    temp2.append(var + '_erf')
                        if len(temp2) > 0:
                            #print "Variables the prestation %s depends of (some missing):\n %s \n" %(varcol.name, str(temp))
                            pass
                        else:
                            #print "Variables the prestation %s depends of couldn't be found :\n %s \n" %(varcol.name, str(temp))
                            pass
                                    
                    if len(temp2) > 0:
                        temp = table[[col, 'idmen'] + temp2][0:10]
                        bigtemp['table'] = pd.merge(temp, bigtemp['table'], how = 'inner')
                        #print temp.to_string(), "\n"
                    if varcol._option != {} and not set(varcol._option.keys()) < set(options_met):
                        vars_to_fetch = list(set(varcol._option.keys())-set(options_met))
                        #print "and the options to current variable %s for the id's with strongest difference :\n %s \n" %(varcol.name, varcol._option.keys())
                        liste = [i for i in range(0,10)]
                        liste = map(lambda x: table['idmen'].iloc[x], liste)
                        temp2 = output_df_nonaggr[['idmen', 'quimen'] 
                                                  + vars_to_fetch][output_df_nonaggr['idmen'].isin(table['idmen'][0:10])]
                        
                        temp3 = temp2[temp2['idmen'] == liste[0]]
                        for i in xrange(1,10):
                            temp3 = temp3.append(temp2[temp2['idmen'] == liste[i]])
                        if bigtemp['options'] is None:
                            bigtemp['options'] = temp3
                        else:
                            bigtemp['options'] = bigtemp['options'].merge(temp3, on = ['idmen','quimen'], how = 'inner')
#                         temp3.set_index(['idmen',  'quimen'], drop = True, inplace = True) # If we do that
                        del temp, temp2, temp3
                        gc.collect()
                            
                    already_met.append(varcol.name)
                    options_met.extend(varcol._option.keys())
                    for var in varcol._parents:
                        iter_on_parents(var)
                        
            iter_on_parents(varcol)
            bigtemp['table']['quimen'] = 0
            # We merge the aggregate table with the option table ( for each individual in entity )
            bigtemp['table'] = bigtemp['table'].merge(bigtemp['options'],
                                                       how = 'right',
                                                        on = ['idmen', 'quimen'],
                                                         suffixes = ('(agg)', '(ind)'))
            bigtemp['table'].set_index(['idmen', 'quimen'], drop = True, inplace = True)
            l = []
            for ident in bigtemp['options']['idmen'].unique():
                l.append(len(bigtemp['options'][bigtemp['options']['idmen']== ident]) - 1)
            # Reshaping the table to group by descending error on col, common entities
            concat1 = bigtemp['table'].ix[0:10]
            concat2 = bigtemp['table'].ix[10:]
            concatene = concat1.ix[0:1].append(concat2.ix[0:l[0]])
            somme = l[0]
            for i in xrange(1,10):
                concatene = concatene.append(concat1.ix[i:i+1].append(concat2.ix[somme:l[i]+somme]))
                somme += l[i]
                
            print "Table of values for %s dependencies : \n" %col
            erf_df_fetched.rename(columns = {'ident':'idmen', 'noi':'quimen'}, inplace = True)
            erf_df_fetched.set_index(['idmen','quimen'], drop = True, inplace = True)
            concatene = concatene.merge(erf_df_fetched,left_index = True, right_index = True , how = 'left', suffixes = ('(concat)','(fetched)'))
            print concatene.to_string()
            del bigtemp['table'], bigtemp['options'], concatene
            gc.collect()    
 
if __name__ == '__main__':
    test()


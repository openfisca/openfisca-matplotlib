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




class Debugger(object):
    def __init__(self):
        super(Debugger, self).__init__()


    def set_simulation(self, simulation):
        self.simulation = simulation

    def set_variable(self, variable):
        self.variable = variable
        
    def show_aggregates(self):
        from src.countries.france.data.erf.aggregates import build_erf_aggregates        
        
        # TODO: test and raise except for existence of self.simulation, self.variable
        variable = self.variable
        of_aggregates = Aggregates()
        of_aggregates.set_simulation(self.simulation)
        of_aggregates.compute()

        temp = (build_erf_aggregates(variables=[variable], year= self.simulation.datesim.year))
        
        label2var, var2label, var2enum = self.simulation.output_table.description.builds_dicts()
        
        selection = of_aggregates.aggr_frame["Mesure"] == var2label[variable] 
        print of_aggregates.aggr_frame[selection] 
        print temp
        # TODO: clean this
        return 


    def preproc(self):
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
        parents = map(lambda x: simulation.output_table.description.get_col(x), variables)
        parents = get_all_ancestors(parents)
        options = []
        for varcol in parents:
            options.extend(varcol._option.keys())
        options = list(set(options))
        #print options
        parents = map(lambda x: x.name, parents)
        for var in variables:
            children = set()
            varcol = simulation.output_table.description.get_col(var)
            children = children.union(set(map(lambda x: x.name, varcol._children)))
        variables = list(set(parents + list(children)))
        #print variables
        del parents, children
        gc.collect()
        
        def get_var(variable):
            variables =[variable]
            return simulation.aggregated_by_entity(entity="men", variables=variables,  
                                                    all_output_vars = False, force_sum=True)[0]
            
        simu_aggr_tables = get_var(variables[0])
        for var in variables[1:]:
            simu_aggr_tables = simu_aggr_tables.merge(get_var(var)[['idmen', var]], on = 'idmen', how = 'outer') 
                                                     
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
        
        fetch_eec = ['statut','titc','chpub','encadr','prosa','age','naim','naia','noindiv']
        fetch_erf = ['zsali','af','ident','wprm','noi','noindiv','quelfic']
        erf_df = erf_data.get_of_values(variables= fetch_erf, table="erf_indivi")
        eec_df = erf_data.get_of_values(variables= fetch_eec, table="eec_indivi")
        erf_eec_indivi = erf_df.merge(eec_df, on ='noindiv', how = 'inner' )
        assert 'quelfic' in erf_eec_indivi.columns, "quelfic not in erf_indivi columns"
        del eec_df, erf_df
    
        # We then get the aggregate variables for the menage ( mainly to compare with of )
        print 'Loading data from erf_menage table'
        erf_menage = erf_data.get_of_values(variables= list(todo) + ['quelfic'], table="erf_menage")
    
        del todo
        gc.collect()
        assert 'ident' in erf_menage.columns, "ident not in erf_menage.columns"
            
        from src.countries.france.data.erf import get_erf2of
        erf2of = get_erf2of()
        erf_menage.rename(columns = erf2of, inplace = True)
        
    # We get the options from the simulation non aggregated tables:
    
        # First from the output_table
        # We recreate the noindiv in output_table
        simulation.output_table.table['noindiv'] = 100 * simulation.output_table.table.idmen_ind + simulation.output_table.table.noi_ind
        simulation.output_table.table['noindiv'] = simulation.output_table.table['noindiv'].astype(np.int64)
        s1 = [var for var in set(options).intersection(set(simulation.output_table.table.columns))] + ['idmen_ind', 'quimen_ind', 'noindiv']
        simu_nonaggr_tables = (simulation.output_table.table)[s1]
        simu_nonaggr_tables.rename(columns = {'idmen_ind' : 'idmen', 'quimen_ind':'quimen'}, inplace = True)
        assert 'noindiv' in simu_nonaggr_tables.columns
        
        # If not found, we dwelve into the input_table
        if (set(s1)- set(['idmen_ind', 'quimen_ind','noindiv'])) < set(options):
            assert 'noindiv' in simulation.input_table.table.columns, "'noindiv' not in simulation.input_table.table.columns"
            s2 = [var for var in (set(options).intersection(set(simulation.input_table.table.columns)) - set(s1))] + ['noindiv']
            #print s2
            temp = simulation.input_table.table[s2]
            simu_nonaggr_tables = simu_nonaggr_tables.merge(temp, on = 'noindiv', how = 'inner', sort = False)
                
            del s2, temp
        del s1
        gc.collect()
        
        simu_nonaggr_tables = simu_nonaggr_tables[list(set(options)) + ['idmen', 'quimen','noindiv']]
        #print options, variables
        assert 'idmen' in simu_nonaggr_tables.columns, 'Idmen not in simu_nonaggr_tables columns'
    
        # Check the idmens that are not common        
        erf_menage.rename(columns = {'ident' : 'idmen'}, inplace = True)
        
        print "\n"
        print 'Checking if idmen is here...'
        print '\n ERF : '
        print 'idmen' in erf_menage.columns
        print "\n Simulation output"
        print 'idmen' in simu_aggr_tables.columns
        print "\n"
    
        #print 'Dropping duplicates of idmen for both tables...'
        assert not erf_menage["idmen"].duplicated().any(), "Duplicated idmen in erf_menage" 
        #erf_menage.drop_duplicates('idmen', inplace = True)
        simu_aggr_tables.drop_duplicates('idmen', inplace = True)
        assert not simu_aggr_tables["idmen"].duplicated().any(), "Duplicated idmen in of"
        
        print 'Checking mismatching idmen... '
        s1 = set(erf_menage['idmen']) - (set(simu_aggr_tables['idmen']))
        if s1:
            print "idmen that aren't in simu_aggr_tables : %s" %str(len(s1))
            pass
        s2 = (set(simu_aggr_tables['idmen'])) - set(erf_menage['idmen'])
        if s2:
            print "idmen that aren't in erf_menage : %s" %str(len(s2))
            pass
        del s1, s2
    
        # Restrict to common idmens and merge
        s3 = set(erf_menage['idmen']).intersection(set(simu_aggr_tables['idmen']))
        print "Restricting to %s common idmen... \n" %str(len(s3))
        erf_menage = erf_menage[erf_menage['idmen'].isin(s3)]
        simu_aggr_tables = simu_aggr_tables[simu_aggr_tables['idmen'].isin(s3)]
        del s3
        gc.collect()
        
        #print erf_menage.columns
        #print simu_aggr_tables.columns
        
        # Compare differences across of and erf dataframes
        print "Comparing differences between dataframes... \n"
        colcom = (set(erf_menage.columns).intersection(set(simu_aggr_tables.columns))) - set(['idmen','wprm'])
        print 'Common variables: '
        print colcom
        erf_menage.reset_index(inplace = True)
        simu_aggr_tables.reset_index(inplace = True)
        for col in colcom:
            temp = set(erf_menage['idmen'][erf_menage[col] != simu_aggr_tables[col]])
            print "Numbers of idmen that aren't equal on variable %s : %s \n" %(col, str(len(temp)))
            del temp

    def describe_discrepancies(self):
        pass


def test(year=2006, variables = ['af']):
    '''
    
    '''
    
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=year, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()
    simulation.compute()

#     of_aggregates = Aggregates()
#     of_aggregates.set_simulation(simulation)
#     of_aggregates.compute()
#     print of_aggregates.aggr_frame
#     
#     from src.countries.france.data.erf.aggregates import build_erf_aggregates
#     temp = (build_erf_aggregates(variables=variables, year= year))
#     print temp
#     return
    variable= "af"
    debugger = Debugger()
    debugger.set_simulation(simulation)
    debugger.set_variable(variable)
    debugger.show_aggregates()
    


    
    
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
    parents = map(lambda x: simulation.output_table.description.get_col(x), variables)
    parents = get_all_ancestors(parents)
    options = []
    for varcol in parents:
        options.extend(varcol._option.keys())
    options = list(set(options))
    #print options
    parents = map(lambda x: x.name, parents)
    for var in variables:
        children = set()
        varcol = simulation.output_table.description.get_col(var)
        children = children.union(set(map(lambda x: x.name, varcol._children)))
    variables = list(set(parents + list(children)))
    #print variables
    del parents, children
    gc.collect()
    
    def get_var(variable):
        variables =[variable]
        return simulation.aggregated_by_entity(entity="men", variables=variables,  
                                                all_output_vars = False, force_sum=True)[0]
        
    simu_aggr_tables = get_var(variables[0])
    for var in variables[1:]:
        simu_aggr_tables = simu_aggr_tables.merge(get_var(var)[['idmen', var]], on = 'idmen', how = 'outer') 
                                                 
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
    
    fetch_eec = ['statut','titc','chpub','encadr','prosa','age','naim','naia','noindiv']
    fetch_erf = ['zsali','af','ident','wprm','noi','noindiv','quelfic']
    erf_df = erf_data.get_of_values(variables= fetch_erf, table="erf_indivi")
    eec_df = erf_data.get_of_values(variables= fetch_eec, table="eec_indivi")
    erf_eec_indivi = erf_df.merge(eec_df, on ='noindiv', how = 'inner' )
    assert 'quelfic' in erf_eec_indivi.columns, "quelfic not in erf_indivi columns"
    del eec_df, erf_df

    # We then get the aggregate variables for the menage ( mainly to compare with of )
    print 'Loading data from erf_menage table'
    erf_menage = erf_data.get_of_values(variables= list(todo) + ['quelfic'], table="erf_menage")

    del todo
    gc.collect()
    assert 'ident' in erf_menage.columns, "ident not in erf_menage.columns"
        
    from src.countries.france.data.erf import get_erf2of
    erf2of = get_erf2of()
    erf_menage.rename(columns = erf2of, inplace = True)
    
# We get the options from the simulation non aggregated tables:

    # First from the output_table
    # We recreate the noindiv in output_table
    simulation.output_table.table['noindiv'] = 100 * simulation.output_table.table.idmen_ind + simulation.output_table.table.noi_ind
    simulation.output_table.table['noindiv'] = simulation.output_table.table['noindiv'].astype(np.int64)
    s1 = [var for var in set(options).intersection(set(simulation.output_table.table.columns))] + ['idmen_ind', 'quimen_ind', 'noindiv']
    simu_nonaggr_tables = (simulation.output_table.table)[s1]
    simu_nonaggr_tables.rename(columns = {'idmen_ind' : 'idmen', 'quimen_ind':'quimen'}, inplace = True)
    assert 'noindiv' in simu_nonaggr_tables.columns
    
    # If not found, we dwelve into the input_table
    if (set(s1)- set(['idmen_ind', 'quimen_ind','noindiv'])) < set(options):
        assert 'noindiv' in simulation.input_table.table.columns, "'noindiv' not in simulation.input_table.table.columns"
        s2 = [var for var in (set(options).intersection(set(simulation.input_table.table.columns)) - set(s1))] + ['noindiv']
        #print s2
        temp = simulation.input_table.table[s2]
        simu_nonaggr_tables = simu_nonaggr_tables.merge(temp, on = 'noindiv', how = 'inner', sort = False)
            
        del s2, temp
    del s1
    gc.collect()
    
    simu_nonaggr_tables = simu_nonaggr_tables[list(set(options)) + ['idmen', 'quimen','noindiv']]
    #print options, variables
    assert 'idmen' in simu_nonaggr_tables.columns, 'Idmen not in simu_nonaggr_tables columns'

    # Check the idmens that are not common        
    erf_menage.rename(columns = {'ident' : 'idmen'}, inplace = True)
    
    print "\n"
    print 'Checking if idmen is here...'
    print '\n ERF : '
    print 'idmen' in erf_menage.columns
    print "\n Simulation output"
    print 'idmen' in simu_aggr_tables.columns
    print "\n"

    #print 'Dropping duplicates of idmen for both tables...'
    assert not erf_menage["idmen"].duplicated().any(), "Duplicated idmen in erf_menage" 
    #erf_menage.drop_duplicates('idmen', inplace = True)
    simu_aggr_tables.drop_duplicates('idmen', inplace = True)
    assert not simu_aggr_tables["idmen"].duplicated().any(), "Duplicated idmen in of"
    
    print 'Checking mismatching idmen... '
    s1 = set(erf_menage['idmen']) - (set(simu_aggr_tables['idmen']))
    if s1:
        print "idmen that aren't in simu_aggr_tables : %s" %str(len(s1))
        pass
    s2 = (set(simu_aggr_tables['idmen'])) - set(erf_menage['idmen'])
    if s2:
        print "idmen that aren't in erf_menage : %s" %str(len(s2))
        pass
    del s1, s2

    # Restrict to common idmens and merge
    s3 = set(erf_menage['idmen']).intersection(set(simu_aggr_tables['idmen']))
    print "Restricting to %s common idmen... \n" %str(len(s3))
    erf_menage = erf_menage[erf_menage['idmen'].isin(s3)]
    simu_aggr_tables = simu_aggr_tables[simu_aggr_tables['idmen'].isin(s3)]
    del s3
    gc.collect()
    
    #print erf_menage.columns
    #print simu_aggr_tables.columns
    
    # Compare differences across of and erf dataframes
    print "Comparing differences between dataframes... \n"
    colcom = (set(erf_menage.columns).intersection(set(simu_aggr_tables.columns))) - set(['idmen','wprm'])
    print 'Common variables: '
    print colcom
    erf_menage.reset_index(inplace = True)
    simu_aggr_tables.reset_index(inplace = True)
    for col in colcom:
        temp = set(erf_menage['idmen'][erf_menage[col] != simu_aggr_tables[col]])
        print "Numbers of idmen that aren't equal on variable %s : %s \n" %(col, str(len(temp)))
        del temp
    
    
    # Detect the biggest differences
    bigtable = merge(erf_menage, simu_aggr_tables, on = 'idmen', how = 'inner', suffixes=('_erf','_of'))
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
        #print table[col][0:10].to_string()
        if bigtemp is None:
            bigtemp = {'table' : table[[col, col+'_of', col+'_erf', 'idmen']][0:10],
                       'options' : None}
        bigtemp['table'][col+'div'] = bigtemp['table'][col+'_of'] / bigtemp['table'][col+'_erf']
        print bigtemp['table'].to_string()
        
        '''
        bigtemp is the table which will get filled little by little by the relevant variables.
        Up to the last rows of code 'table' refers to a table of aggregated values, 
        while 'options is a table of individual variables.
        The reason we call it in a dictionnary is also because we modify it inside the recursive function 'iter_on parents',
        and it causes an error in Python unless for certain types like dictionnary values.
        '''
        #print "\n"
        
        # If variable is a Prestation, we show the dependancies
        varcol = simulation.output_table.description.get_col(col)
        if isinstance(varcol, Prestation):
            
            '''
            For the direct children
            '''
            if not varcol._children is None:
                ch_to_fetch = list(varcol._children)
                ch_to_fetch = map(lambda x: x.name, ch_to_fetch)
                ch_fetched = []
                    
                if set(ch_to_fetch) <= set(simu_aggr_tables.columns):
                    print "Variables which need %s to be computed :\n %s \n" %(col, str(ch_to_fetch))
                    for var in ch_to_fetch:
                        if var + '_of' in table.columns:
                            ch_fetched.append(var + '_of')
                        else:
                            ch_fetched.append(var)
                elif set(ch_to_fetch) <= set(simu_aggr_tables.columns).union(erf_menage.columns):
                    print "Variables which need %s to be computed (some missing picked in erf):\n %s \n" %(col, str(ch_to_fetch))
                    for var in ch_to_fetch:
                        if var in simu_aggr_tables.columns:
                            if var + '_of' in table.columns:
                                ch_fetched.append(var + '_of')
                        elif var + '_erf' in table.columns:
                                ch_fetched.append(var + '_erf')
                        else:
                            ch_fetched.append(var)
                else:
                    print "Variables which need %s to be computed (some missing):\n %s \n" %(col, str(ch_to_fetch))
                    for var in ch_to_fetch:
                
                        if var in simu_aggr_tables.columns:
                            if var + '_of' in table.columns:
                                ch_fetched.append(var + '_of')
                        elif var in erf_menage.columns:
                            if var + '_erf' in table.columns:
                                ch_fetched.append(var + '_erf')
                                
                print table[[col] + ch_fetched][0:10]
                print "\n"
                del ch_to_fetch, ch_fetched
                
            '''
            For the parents
            '''
            def iter_on_parents(varcol):
                if (varcol._parents == set() and varcol._option == {}) or varcol.name in already_met:
                    return
                else:
                    par_to_fetch = list(varcol._parents)
                    par_to_fetch = map(lambda x: x.name, par_to_fetch)
                    par_fetched = []
                        
                    if set(par_fetched) <= set(simu_aggr_tables.columns):
                        #print "Variables the prestation %s depends of :\n %s \n" %(varcol.name, str(par_fetched))
                        for var in par_fetched:
                            if var + '_of' in table.columns:
                                par_fetched.append(var + '_of')
                            else:
                                par_fetched.append(var)
                    elif set(par_fetched) <= set(simu_aggr_tables.columns).union(erf_menage.columns):
                        #print "Variables the prestation %s depends of (some missing picked in erf):\n %s \n" %(varcol.name,str(par_fetched))
                        for var in par_fetched:
                            if var in simu_aggr_tables.columns:
                                if var + '_of' in table.columns:
                                    par_fetched.append(var + '_of')
                            elif var + '_erf' in table.columns:
                                    par_fetched.append(var + '_erf')
                            else:
                                par_fetched.append(var)
                    else:
                        for var in par_fetched:
                            if var in simu_aggr_tables.columns:
                                if var + '_of' in table.columns:
                                    par_fetched.append(var + '_of')
                            elif var in erf_menage.columns:
                                if var + '_erf' in table.columns:
                                    par_fetched.append(var + '_erf')
                        if len(par_fetched) > 0:
                            #print "Variables the prestation %s depends of (some missing):\n %s \n" %(varcol.name, str(par_fetched))
                            pass
                        else:
                            #print "Variables the prestation %s depends of couldn't be found :\n %s \n" %(varcol.name, str(par_fetched))
                            pass
                                    
                    if len(par_fetched) > 0:
                        temp = table[[col, 'idmen'] + par_fetched][0:10]
                        bigtemp['table'] = pd.merge(temp, bigtemp['table'], how = 'inner')
                        #print temp.to_string(), "\n"
                    if varcol._option != {} and not set(varcol._option.keys()) < set(options_met):
                        vars_to_fetch = list(set(varcol._option.keys())-set(options_met))
                        #print "and the options to current variable %s for the id's with strongest difference :\n %s \n" %(varcol.name, varcol._option.keys())
                        liste = [i for i in range(0,10)]
                        liste = map(lambda x: table['idmen'].iloc[x], liste)
                        temp = simu_nonaggr_tables[['idmen', 'quimen','noindiv'] 
                                                  + vars_to_fetch][simu_nonaggr_tables['idmen'].isin(table['idmen'][0:10])]
                        
                        temp_sorted = temp[temp['idmen'] == liste[0]]
                        for i in xrange(1,10):
                            temp_sorted = temp_sorted.append(temp[temp['idmen'] == liste[i]])
                        if bigtemp['options'] is None:
                            bigtemp['options'] = temp_sorted
                            bigtemp['options'] = bigtemp['options'].merge(erf_eec_indivi, on = 'noindiv', how = 'outer')
                        else:
                            bigtemp['options'] = bigtemp['options'].merge(temp_sorted, on = ['noindiv','idmen','quimen'], how = 'outer')
#                         temp_sorted.set_index(['idmen',  'quimen'], drop = True, inplace = True) # If we do that
                        del temp, temp_sorted
                        gc.collect()
                            
                    already_met.append(varcol.name)
                    options_met.extend(varcol._option.keys())
                    for var in varcol._parents:
                        iter_on_parents(var)
                        
            iter_on_parents(varcol)
            # We merge the aggregate table with the option table ( for each individual in entity )
            bigtemp['table'] = bigtemp['table'].merge(bigtemp['options'],
                                                       how = 'left',
                                                        on = 'idmen',
                                                         suffixes = ('(agg)', '(ind)'))
            
            # Reshaping the table to group by descending error on col, common entities
            bigtemp['table'].sort(columns = ['af','quimen'], ascending = [False,True], inplace = True)
            bigtemp['table'] = bigtemp['table'].groupby(['idmen','quimen'], sort = False).sum()
            print "Table of values for %s dependencies : \n" %col
            print bigtemp['table'].to_string()
            del bigtemp['table'], bigtemp['options']
            gc.collect()    
 
if __name__ == '__main__':
    test()


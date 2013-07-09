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
from pandas import ExcelWriter, HDFStore, DataFrame, merge
import os
import numpy as np
import gc

from src.lib.utils import mark_weighted_percentiles as mwp
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from src.countries.france.data.erf.datatable import DataCollection
from src.lib.datatable import DataTable


country= "france"
from src import SRC_PATH

def test(year=2006):
    
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=year, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()
    simulation.compute()
#    output_df = simulation.output_table.table
    
    variables = ["af"]  
    output_df = simulation.aggregated_by_entity(entity="men", variables=variables,  
                                                all_output_vars = False, force_sum=True)[0]


    erf_data = DataCollection(year=year)
    erf_df = erf_data.get_of_values(variables=variables + ["ident", "wprm"], table="erf_menage")
    from src.countries.france.data.erf import get_erf2of
    erf2of = get_erf2of()
    erf_df.rename(columns = erf2of, inplace = True)


    # Check the idmens that are not common        
    erf_df.rename(columns = {'ident' : 'idmen'}, inplace = True)
    # <=============== MODIFY HERE TO STUDY =/= ENTITIES ====================>
    
    print "\n"
    print 'Checking if idmen is here...'
    print erf_df
    print 'idmen' in erf_df.columns
    print output_df
    print 'idmen' in output_df.columns
    print "\n"

    print 'Dropping duplicates of idmen for both tables...'
    assert not erf_df["idmen"].duplicated().any(), "Duplicated idmen in erf" 
    #erf_df.drop_duplicates('idmen', inplace = True)
    output_df.drop_duplicates('idmen', inplace = True)
    assert not output_df["idmen"].duplicated().any(), "Duplicated idmen in of"
    
    print 'Checking mismatching idmen... '
    s1 = set(erf_df['idmen']) - (set(output_df['idmen']))
    if s1:
        print "idmen that aren't in output_df : %s" %str(len(s1))
    s2 = (set(output_df['idmen'])) - set(erf_df['idmen'])
    if s2:
        print "idmen that aren't in erf_df : %s" %str(len(s2))
    del s1, s2

    # Restrict to common idmens and merge
    s3 = set(erf_df['idmen']).intersection(set(output_df['idmen']))
    print "Restricting to %s common idmen... \n" %str(len(s3))
    erf_df = erf_df[erf_df['idmen'].isin(s3)]
    output_df = output_df[output_df['idmen'].isin(s3)]
    del s3
    gc.collect()
    
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
    table = merge(erf_df, output_df, on = 'idmen', how = 'inner', suffixes=('_erf','_of'))
    print 'Length of new dataframe is %s' %str(len(table))
    del erf_df, output_df
    gc.collect()
    varname_of  = variables[0]+"_of"
    varname_erf = variables[0]+"_erf"
    from numpy import logical_and as and_
    table = table[and_(table[varname_of]!=0,table[varname_erf]!=0)] 
    for col in colcom:
        table[col] = (table[col+'_erf'] - table[col+'_of']) # / table[col+'_erf'] #Difference relativ
        table[col] = table[col].apply(lambda x: abs(x))
        print 'Minimum difference between the two tables for %s     is %s' %(col, str(table[col].min()))
        print 'Maximum difference between the two tables for %s is %s' %(col, str(table[col].max()))
        print table[col].describe()
        print table
        try:
            dec, values = mwp(table[col].astype("float"), np.arange(1,11), table['wprm_erf'].astype("float"), 2, return_quantiles=True)
            print sorted(values)
            dec, values = mwp(table[col].astype("float"), np.arange(1,101), table['wprm_erf'].astype("float"), 2, return_quantiles=True)
            print sorted(values)[90:]
            del dec, values
            gc.collect()
        except:
            print 'Weighted percentile method didnt work for %s' %col
        print "\n"
    
    # Show the relevant information for the most deviant households
        table.sort(columns = col, ascending = False, inplace = True)
        print table[['idmen', col]][0:100].to_string() #Should print the idmen along with col by descreasing number of discrapencies
        print "\n"
    
    
    var = variables[0]
    varcol = simulation.get_col(var)
    for varcol in varcol._parents:
        print varcol.name
    
 
if __name__ == '__main__':
    test()


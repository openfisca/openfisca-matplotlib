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
    output_df = simulation.output_table.table
    
#     variable = "af"  
#     of_df = simulation.aggregated_by_entity(entity="men", variables=variable,  force_sum=True)
#     print of_df
#     print isinstance(of_df, DataFrame)
#     print isinstance(of_df, DataTable)

    erf_data = DataCollection(year=year)
    erf_df = erf_data.get_of_values(table="erf_menage") #, variable
    from src.countries.france.data.erf import get_erf2of
    erf2of = get_erf2of()
    erf_df.rename(columns = erf2of, inplace = True)
    print isinstance(erf_df, DataFrame)
    print isinstance(erf_df, DataTable)

    # Check the idmens that are not common
    output_df.rename(columns = {'idmen_ind' : 'idmen', 'wprm_ind' : 'wprm'}, inplace = True)
    erf_df.rename(columns = {'ident' : 'idmen'}, inplace = True)
    # <=============== MODIFY HERE TO STUDY =/= ENTITIES ====================>
    
    print "\n"
    print 'Checking if idmen is here...'
    print 'idmen' in erf_df.columns
    print 'idmen' in output_df.columns
    print "\n"
    
    print 'Dropping duplicates of idmen for both tables...'
    erf_df.drop_duplicates('idmen', inplace = True)
    output_df.drop_duplicates('idmen', inplace = True)
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
    bigtable = merge(erf_df, output_df, on = 'idmen', how = 'inner', suffixes=('_erf','_of'))
    print 'Length of new dataframe is %s' %str(len(bigtable))
#     del erf_df, output_df
#     gc.collect()
    for col in colcom:
#         temp = (bigtable[col+'_erf'] - bigtable[col+'_of']) / bigtable[col+'_erf']
#         temp1 = np.isinf(temp)
#         temp3 = bigtable[col+'_of'] == 0
#         print temp3.dtype
#         temp2 = bigtable[col+'_erf'] == 0
#         print np.array_equiv(temp2,temp3)
#         assert np.array_equiv(temp1, temp2), 'Errors in relative diff.'
#         del temp1, temp2
#         gc.collect()
        bigtable[col] = (bigtable[col+'_erf'] - bigtable[col+'_of']) # / bigtable[col+'_erf'] #Difference relativ
        bigtable[col] = bigtable[col].apply(lambda x: abs(x))
        print 'Minimum difference between the two tables for %s     is %s' %(col, str(bigtable[col].min()))
        print 'Maximum difference between the two tables for %s is %s' %(col, str(bigtable[col].max()))
        print bigtable[col].describe()
        try:
            dec, values = mwp(bigtable[col], np.arange(1,11), bigtable['wprm_erf'], 2, return_quantiles=True)
            print sorted(values)
            dec, values = mwp(bigtable[col], np.arange(1,101), bigtable['wprm_erf'], 2, return_quantiles=True)
            print sorted(values)[90:]
            del dec, values
            gc.collect()
        except:
            print 'Weighted percentile method didnt work for %s' %col
        print "\n"
    
    # Show the relevant information for the most deviant households
        bigtable.sort(column = col, ascending = False, inplace = True)
        print bigtable[['idmen', col]][0:10] #Should print the idmen along with col by descreasing number of discrapencies
        print "\n"
        
        # If variable is a Prestation, we show the dependancies
        from src.lib.columns import Prestation
        varcol = varcol  = simulation.output_table.description.get_col(col)
        if isinstance(varcol, Prestation):
            temp = list(varcol._parents)
            temp = map(lambda x: x.name, temp)
                
            if set(temp) <= set(output_df.columns):
                print "Variables the prestation %s depends of :" %col
                for i in xrange(len(temp)):
                    if temp[i] + '_of' in bigtable.columns:
                        temp[i] += '_of'
            elif set(temp) <= set(output_df.columns).union(erf_df.columns):
                print "Variables the prestation %s depends of (some missing picked in erf):" %col
                for i in xrange(len(temp)):
                    var = temp[i]
                    if var in output_df.columns:
                        if var + '_of' in bigtable.columns:
                            var = var + '_of'
                    else:
                        if var + '_erf' in bigtable.columns:
                            var = var + '_erf'
                    temp[i] = var
            else:
                print "Variables the prestation %s depends of (some missing):" %col
                for i in xrange(len(temp)):
                    var = temp[i]
                    if var in output_df.columns:
                        if var + '_of' in bigtable.columns:
                            var = var + '_of'
                    elif var in erf_df.columns:
                        if var + '_erf' in bigtable.columns:
                            var = var + '_erf'
                    else:
                        temp.remove(var)
                    temp[i] = var
    #             temp = list(varcol._parents)
    #             for cp in temp:
    #                 cp = cp.name
            print bigtable[['idmen', col] + temp][0:10]
            print "\n"
#             if varcol._children <= simulation.output_table.description.columns:
#                 print "Prestations which need %s to be computed :" %col
#     #             temp = list(varcol._children)
#     #             for cp in temp:
#     #                 cp = cp.name
#                 print bigtable[['idmen', col] + temp][0:10]
#                 print "\n"
    
    
 
if __name__ == '__main__':
    test()


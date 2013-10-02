# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simulation

from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from pandas import ExcelWriter
import os
from src.countries.france.data.erf.aggregates import build_erf_aggregates
import pandas as pd

import gc
import random

try:
    import xlwt
    from src.countries.france.XL import XLtable
except:
    pass



# from src.scripts.validation.check_consistency_tests import ( check_inputs_enumcols,
#                                                               check_entities,
#                                                               check_weights)

country = 'france'

from src import SRC_PATH


class Recap(object):
    def __init__(self):
        super(Recap, self).__init__()
        self.country = None 
        self.years = None
        self.aggregates_variables = None
        self.sources = None
        self.survey_filename = None

    def set_country(self, country):
        self.country = country

    def set_years(self, years):
        self.years= years
        
    def set_aggregates_variables(self, variables):
        self.aggregates_variables = variables
        
    def set_sources(self, sources):
        self.sources = sources
    
    def set_survey_filename(self, survey_filename):
        self.survey_filename = survey_filename
        
    def _build_multiindex(self):
        variables = self.aggregates_variables
        sources = self.sources
        years = self.years
        print variables
        print sources
        print years
#        print [zip(variable, source, year) for variable in variables, source in sources, year in years]    
        index = list()
        for variable in variables:
            for source in sources:
                for year in years:
                    index.append((variable, source, year))
                    
        from pandas.core.index import MultiIndex
        self.index = MultiIndex.from_tuples(index, names = ['measure', 'source', 'year'])
               
    def _generate_aggregates(self):
        dfs = list()
        dfs_erf = list()
        years = self.years
        country = self.country
        for year in years:
            # Running a standard SurveySimulation to get OF aggregates
            simulation = SurveySimulation()
            survey_filename = self.survey_filename
            simulation.set_config(year=year, country=country, 
                                  survey_filename=survey_filename)
            simulation.set_param()
            simulation.compute()
            agg = Aggregates()
            agg.set_simulation(simulation)
            agg.compute()
            df = agg.aggr_frame
            df['year'] = year
            label2var, var2label, var2enum = simulation.output_table.description.builds_dicts()
            #colonnes = simulation.output_table.table.columns
            dfs.append(df)
            variables = agg.varlist
            labels_variables = map(lambda x: var2label[x], variables)
            del simulation, agg, var2enum, df
            # simulation.save_content(name, filename)
            
            gc.collect()

            # ERFS
            temp = (build_erf_aggregates(variables=variables, year= year))
            temp.rename(columns = var2label, inplace = True)
            temp = temp.T
            temp.reset_index(inplace = True)
            temp['year'] = year
            dfs_erf.append(temp)
            del temp
            gc.collect()

        self.labels_variables = labels_variables
        self.aggregates_of_dataframe = dfs 
        self.aggregates_erfs_dataframe = dfs_erf
        
    def _reshape_tables(self):
        """
        TODO _reshape_tables should be cleaned !!!
        """
        dfs = self.aggregates_of_dataframe
        dfs_erf = self.aggregates_erfs_dataframe
        labels_variables = self.labels_variables
        
        agg = Aggregates()
         
        # We need this for the columns labels to work
        
        print 'Resetting index to avoid later trouble on manipulation'
        for d in dfs:
            d.reset_index(inplace = True)
            d.set_index('Mesure', inplace = True, drop = False)
            d.reindex_axis(labels_variables, axis = 0)
            d.reset_index(inplace = True, drop = True)
#             print d.to_string()
        for d in dfs_erf:
            d.reset_index(inplace = True)
            d['Mesure'] = agg.labels['dep']
            d.set_index('index', inplace = True, drop = False)
            d.reindex_axis(agg.labels.values(), axis = 0)
            d.reset_index(inplace = True, drop = True)
#             print d.to_string()
            
        # Concatening the openfisca tables for =/= years

        temp = dfs[0]        
        if len(dfs) != 1:
            for d in dfs[1:]:
                temp = pd.concat([temp,d], ignore_index = True)

        
        del temp[agg.labels['entity']], temp['index']
        gc.collect()
        
        print 'We split the real aggregates from the of table'
        temp2 = temp[[agg.labels['var'], agg.labels['benef_real'], agg.labels['dep_real'], 'year']]
        del temp[agg.labels['benef_real']], temp[agg.labels['dep_real']]
        sauvegarde = temp.columns.get_level_values(0).unique()
        temp['source'] = 'of'
        temp2['source'] = 'reel'
        temp2.rename(columns = {agg.labels['benef_real'] : agg.labels['benef'],
                                agg.labels['dep_real'] : agg.labels['dep']}, 
                     inplace = True)
        temp = pd.concat([temp,temp2], ignore_index = True)
        
        print 'We add the erf data to the table'
        for df in dfs_erf:
            del df['level_0'], df['Mesure']
            df.rename(columns = {'index' : agg.labels['var'], 1 : agg.labels['dep']}, inplace = True)
        
        
        temp3 = dfs_erf[0]        
        if len(dfs) != 1:
            for d3 in dfs_erf[1:]:
                temp3 = pd.concat([temp3, d3], ignore_index = True)
        
        temp3['source'] = 'erfs'
        gc.collect()
        temp = pd.concat([temp, temp3], ignore_index = True)
#         print temp.to_string()
        
        print 'Index manipulation to reshape the output'
        temp.reset_index(drop = True, inplace = True)
        # We set the new index
#         temp.set_index('Mesure', drop = True, inplace = True)
#         temp.set_index('source', drop = True, append = True, inplace = True)
#         temp.set_index('year', drop = False, append = True, inplace = True)
        temp = temp.groupby(by=["Mesure", "source", "year"], sort = False).sum()
        # Tricky, the [mesure, source, year] index is unique so sum() will return the only value
        # Groupby automatically deleted the source, mesure... columns and added them to index
        assert(isinstance(temp, pd.DataFrame))
#         print temp.to_string()
        
        # We want the years to be in columns, so we use unstack
        temp_unstacked = temp.unstack()
        # Unfortunately, unstack automatically sorts rows and columns, we have to reindex the table :
        
        ## Reindexing rows
        from pandas.core.index import MultiIndex
        indtemp1 = temp.index.get_level_values(0)
        indtemp2 = temp.index.get_level_values(1)
        indexi = zip(*[indtemp1, indtemp2])
        indexi_bis = []
        for i in xrange(0,len(indexi)):
            if indexi[i] not in indexi_bis:
                indexi_bis.append(indexi[i])
        indexi = indexi_bis
        del indexi_bis
        indexi = MultiIndex.from_tuples(indexi, names = ['Mesure', 'source'])
#         import pdb
#         pdb.set_trace()
        temp_unstacked = temp_unstacked.reindex_axis(indexi, axis = 0) # axis = 0 for rows, 1 for columns
        
        ## Reindexing columns
        # TODO : still not working
        col_indexi = []
        print temp.columns
        for i in xrange(len(sauvegarde)):
#         for col in temp.columns.get_level_values(0).unique():
            col = sauvegarde[i]
            for yr in self.years:
                col_indexi.append((col, yr))
        col_indexi = MultiIndex.from_tuples(col_indexi)
#         print col_indexi
#         print temp_unstacked.columns
        print col_indexi
        print temp_unstacked.columns
        temp_unstacked = temp_unstacked.reindex_axis(col_indexi, axis = 1)
        
        # Our table is ready to be turned to Excel worksheet !
#         print temp_unstacked.to_string()
        del temp_unstacked['Mesure'], temp_unstacked['year']
        temp_unstacked.fillna(0, inplace = True)
        return temp_unstacked

    def build_dataframe(self):
        self._generate_aggregates()
        self.dataframe = self._reshape_tables()

    def save(self):
        
        save_as_xls(self.dataframe, alter_method = False)
        
        

 
def test_recap():
    years = [2006] + range(2008, 2010)
    country = 'france'
    variables = ['cotsoc', 'af']
    sources = ['of', 'erfs', 'reel']
    recap = Recap()
    recap.set_country(country)
#    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
#    recap.set_survey_filename(survey_filename)
    recap.set_years(years)
    recap.set_aggregates_variables(variables)
    recap.set_sources(sources)
    recap._build_multiindex()
    recap.build_dataframe()
    print recap.dataframe.to_string()
    
    
    
    
def test_laurence():
    '''
    Computes the openfisca/real numbers comparaison table in excel worksheet.
    
    Warning: To add more years you'll have to twitch the code manually. 
    Default is years 2006 to 2009 included.
    '''
    def save_as_xls(df, alter_method = True):
        # Saves a datatable under Excel table using XLtable
        if alter_method:
            filename = "C:\desindexation.xls"
            print filename
            writer = ExcelWriter(str(filename))
            df.to_excel(writer)
            writer.save()
        else:
            # XLtable utile pour la mise en couleurs, reliefs, etc. de la table, inutile sinon
            stxl = XLtable(df)
            # <========== HERE TO CHANGE OVERLAY ======>
            wb = xlwt.Workbook()
            ws = wb.add_sheet('resultatstest')
            erfxcel = stxl.place_table(ws)
            try: # I dunno more clever commands
                wb.save("C:\outputtest.xls")
            except:
                n = random.randint(0,100)
                wb.save("C:\outputtest_"+str(n)+".xls")
    
#===============================================================================
#     from numpy.random import randn
#     mesures = ['cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add', 
#                'cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add', 
#                'cotsoc','af', 'add', 'cotsoc','af', 'add', 'cotsoc','af', 'add']
#     sources = ['of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel',
#                'of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel',
#                'of', 'of', 'of', 'erfs', 'erfs', 'erfs', 'reel', 'reel', 'reel']
#     year = ['2006', '2006', '2006', '2006', '2006', '2006', '2006', '2006', '2006',
#             '2007', '2007', '2007', '2007', '2007', '2007', '2007', '2007', '2007',
#             '2008', '2008', '2008', '2008', '2008', '2008', '2008', '2008', '2008']
#     ind = zip(*[mesures,sources, year])
# #     print ind
#     from pandas.core.index import MultiIndex
#     ind = MultiIndex.from_tuples(ind, names = ['mesure', 'source', 'year'])
# #     print ind
#     d = pd.DataFrame(randn(27,2), columns = ['Depenses', 'Recettes'], index = ind)
#     d.reset_index(inplace = True, drop = False)
#     d = d.groupby(by = ['mesure', 'source', 'year'], sort = False).sum()
#     print d
#     d_unstacked = d.unstack()
#     print d
#     indtemp1 = d.index.get_level_values(0)
#     indtemp2 = d.index.get_level_values(1)
#     indexi = zip(*[indtemp1, indtemp2])
#     print indexi
#     indexi_bis = []
#     for i in xrange(len(indexi)):
#         if indexi[i] not in indexi_bis:
#             indexi_bis.append(indexi[i])
#     indexi = indexi_bis
#     indexi = MultiIndex.from_tuples(indexi, names = ['Mesure', 'source'])
#     print indexi
#     d_unstacked = d_unstacked.reindex_axis(indexi, axis = 0)
#     print d_unstacked.to_string()
#     save_as_xls(d_unstacked)
#     return
#===============================================================================
    



    dfs = []
    dfs_erf = []
    for i in range(2006,2010):
        year = i
        yr = str(i)
        # Running a standard SurveySim to get aggregates
        simulation = SurveySimulation()
        survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
        simulation.set_config(year=yr, country=country, 
                              survey_filename=survey_filename)
        simulation.set_param()
        simulation.compute()
        agg = Aggregates()
        agg.set_simulation(simulation)
        agg.compute()
        df = agg.aggr_frame
        df['year'] = year
        label2var, var2label, var2enum = simulation.output_table.description.builds_dicts()
        colonnes = simulation.output_table.table.columns
        dfs.append(df)
        variables = agg.varlist
        labels_variables = map(lambda x: var2label[x], variables)
        del simulation, agg, var2enum, df
        gc.collect()
        
        #Getting ERF aggregates from ERF table
        temp = (build_erf_aggregates(variables=variables, year= year))
        temp.rename(columns = var2label, inplace = True)
        temp = temp.T
        temp.reset_index(inplace = True)
        temp['year'] = year
        dfs_erf.append(temp)
        del temp
        gc.collect()
        print 'Out of data fetching for year ' + str(year)
    print 'Out of data fetching'
    datatest = 3
#     datatest = reshape_tables(dfs, dfs_erf)
    save_as_xls(datatest, alter_method = False)
       
        
if __name__ == '__main__':
    test_recap()
#     year = 2006
#     dfs_erf = build_erf_aggregates(variables =["af"], year=year)
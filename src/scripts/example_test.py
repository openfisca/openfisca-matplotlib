# -*- coding:utf-8 -*-# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


# Exemple of a simple simulation

from src.lib.simulation import ScenarioSimulation
from src.lib.simulation import SurveySimulation
from src.plugins.survey.aggregates import Aggregates
from datetime import datetime
from pandas import ExcelWriter, HDFStore
import os
from src.countries.france.data.erf.aggregates import build_erf_aggregates

import pandas as pd
import numpy as np
import xlwt as xlwt
import xlwt.Style as Style
class XLtable(pd.DataFrame):
    def __init__(self, df=None):
        """
        pandas DataFrame with extra methods for setting location and xlwt style
        in an Excel spreadsheet.

        Parameters
        ----------
        df : A pandas DataFrame object

        Example
        -------
        >>> xldata = XLtable(df=data)
        """
        super(XLtable, self).__init__()
        self._data = df._data
        if isinstance(self.columns, pd.MultiIndex):
            self.col_depth = len(self.columns.levels)
        else:
            self.col_depth = 1
        if isinstance(self.index, pd.MultiIndex):
            self.row_depth = len(self.index.levels)
        else:
            self.row_depth = 1
        # xlwt can't handle int64, so we convert it to float64
        idx = self.dtypes[self.dtypes == np.int64].index
        for i in idx:
            self[i] = self[i].astype(np.float64)
        # we need to convert row indexes too
        if isinstance(self.index, pd.MultiIndex):
            for i in range(len(self.index.levels)):
                if self.index.levels[i].dtype == np.int64:
                    self.index.levels[i] = self.index.levels[i].astype(np.float64)
        else:
            if self.index.dtype.type == np.int64:
                self.index = self.index.astype(np.float64)
        # and column indexes
        if isinstance(self.columns, pd.MultiIndex):
            for i in range(len(self.columns.levels)):
                if self.columns.levels[i].dtype == np.int64:
                    self.columns.levels[i] = self.columns.levels[i].astype(np.float64)
        else:
            if self.columns.dtype.type == np.int64:
                self.columns = self.columns.astype(np.float64)
    def place_index(self, ws, row=0, col=0, axis=0, style=Style.default_style):
        """
        Write XLtable row or column names (indexes) into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the index will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the index will be placed
            (integer, base 0, default 0)
        axis: Whether the row or column index is desired
            (0 for row or 1 for column, default 0)
        style: An xlwt style object

        Example
        -------
        >>> XLtable.place_index(ws=Sheet1, row=0, col=0, axis=0, style=hstyle)

        """
        if axis == 0:
            depth = self.row_depth
            index = self.index
        elif axis == 1:
            depth = self.col_depth
            index = self.columns
        else:
            raise ValueError("XLTable has only two axis (0 or 1)")
        if depth == 1:
            if axis == 0:
                for i in range(len(index)):
                    ws.row(row + i).write(col, index[i], style)
            elif axis == 1:
                for i in range(len(index)):
                    ws.row(row).write(col + i, index[i], style)
        else:
            if axis == 0:
                for level in range(self.row_depth):
                    col += level
                    for i in range(len(index)):
                        ws.row(row + i).write(col, index[i][level], style)
            elif axis == 1:
                for level in range(depth):
                    row += level
                    for i in range(len(index)):
                        ws.row(row).write(col + i, index[i][level], style)
    def place_data(self, ws, row=0, col=0, style=Style.default_style):
        """
        Write XLtable data into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the data will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the data will be placed
            (integer, base 0, default 0)
        style: An xlwt style object

        Example
        -------
        >>> XLtable.place_data(ws=Sheet1, row=0, col=0, style=dstyle)

        """
        for irow in range(len(self.index)): # data
            for icol in range(len(self.columns)):
                ws.row(row + irow).write((col + icol),
                       self.ix[self.index[irow]][self.columns[icol]], style)
    def place_table(self, ws, row=0, col=0, rstyle=Style.default_style,
                    cstyle=Style.default_style, dstyle=Style.default_style):
        """
        Write XLtable (indexes and data) into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the index will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the index will be placed
            (integer, base 0, default 0)
        rstyle: An xlwt style object, determines row index style
        cstyle: An xlwt style object, determines column index style
        dstyle: An xlwt style object, determines data style

        Example
        -------
        >>> XLtable.place_index(ws=Sheet1, row=0, col=0, rstyle=hstyle,
            cstyle=hstyle, dstyle=data_style)

        """
        drow = row + self.col_depth
        dcol = col + self.row_depth
        self.place_index(ws=ws, row=drow, col=col, axis=0, style=rstyle)
        self.place_index(ws=ws, row=row, col=dcol, axis=1, style=cstyle)
        self.place_data(ws=ws, row=drow, col=dcol, style=dstyle)

class XLseries(pd.Series):
    def __new__(cls, *args, **kwargs):
        arr = pd.Series.__new__(cls, *args, **kwargs)
        # xlwt can't handle int64, so we convert it to float64
        if arr.dtype.type == np.int64:
            arr = arr.astype(np.float64)
        # we need to convert indexes too
        if isinstance(arr.index, pd.MultiIndex):
            for i in range(len(arr.index.levels)):
                if arr.index.levels[i].dtype == np.int64:
                    arr.index.levels[i] = arr.index.levels[i].astype(np.float64)
        else:
            if arr.index.dtype.type == np.int64:
                arr.index = arr.index.astype(np.float64)
        return arr.view(XLseries)
    def __init__(self, series=None):
        """
        pandas Series with extra methods for setting location and xlwt style
        in an Excel spreadsheet.

        Parameters
        ----------
        df : A pandas Series object

        Example
        -------
        >>> xlvector = XLseries(series=vector)
        """
        if isinstance(self.index, pd.MultiIndex):
            self.index_depth = len(self.index.levels)
        else:
            self.index_depth = 1
    def place_index(self, ws, row=0, col=0, axis=0, style=Style.default_style):
        """
        Write XLseries index into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the index will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the index will be placed
            (integer, base 0, default 0)
        axis: Whether the index will be placed in vertical or horizontal
            (0 for vertical or 1 for horizontal, default 0)
        style: An xlwt style object

        Example
        -------
        >>> XLseries.place_index(ws=Sheet1, row=0, col=0, axis=0, style=hstyle)

        """
        depth = self.index_depth
        index = self.index
        if axis not in [0,1]:
            raise ValueError("Excel has only two axis (0 or 1)")
        if depth == 1:
            if axis == 0:
                for i in range(len(index)):
                    ws.row(row + i).write(col, index[i], style)
            elif axis == 1:
                for i in range(len(index)):
                    ws.row(row).write(col + i, index[i], style)
        else:
            if axis == 0:
                for level in range(depth):
                    col += level
                    for i in range(len(index)):
                        ws.row(row + i).write(col, index[i][level], style)
            elif axis == 1:
                for level in range(depth):
                    row += level
                    for i in range(len(index)):
                        ws.row(row).write(col + i, index[i][level], style)
    def place_data(self, ws, row=0, col=0, axis=0, style=Style.default_style):
        """
        Write XLseries data into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the data will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the data will be placed
            (integer, base 0, default 0)
        axis: Whether the index will be placed in vertical or horizontal
            (0 for vertical or 1 for horizontal, default 0)
        style: An xlwt style object

        Example
        -------
        >>> XLseries.place_data(ws=Sheet1, row=0, col=0, style=dstyle)

        """
        if axis == 0:
            for i in range(len(self)):
                ws.row(row + i).write(col, self.view(np.ndarray)[i], style)
        elif axis == 1:
            for i in range(len(self)):
                ws.row(row).write(col + i, self.view(np.ndarray)[i], style)
    def place_series(self, ws, row=0, col=0, axis=0,
                     istyle=Style.default_style, dstyle=Style.default_style):
        """
        Write XLseries (index and data) into an Excel sheet

        Parameters
        ----------
        ws : An xlwt Worksheet object
        row: The starting row in Excel where the index will be placed
            (integer, base 0, default 0)
        col: The starting column in Excel where the index will be placed
            (integer, base 0, default 0)
        axis: Whether the series will be placed in vertical or horizontal
            (0 for vertical or 1 for horizontal, default 0)
        istyle: An xlwt style object, determines index style
        dstyle: An xlwt style object, determines data style

        Example
        -------
        >>> XLseries.place_index(ws=Sheet1, row=0, col=0, istyle=hstyle,
            dstyle=data_style)

        """
        self.place_index(ws=ws, row=row, col=col, axis=axis, style=istyle)
        if axis == 0:
            col = col + self.index_depth
        else:
            row = row + self.index_depth
        self.place_data(ws=ws, row=row, col=col, axis=axis, style=dstyle)
        

# from src.scripts.validation.check_consistency_tests import ( check_inputs_enumcols,
#                                                               check_entities,
#                                                               check_weights)

country = 'france'
# destination_dir = "c:/users/utilisateur/documents/"
# fname_all = "aggregates_inflated_loyers.xlsx"
# fname_all = os.path.join(destination_dir, fname_all)              

from src import SRC_PATH
    

def survey_case(year = 2006): 
    yr = str(year)
#        fname = "Agg_%s.%s" %(str(yr), "xls")
    simulation = SurveySimulation()
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    simulation.set_config(year=yr, country=country, 
                          survey_filename=survey_filename)
    simulation.set_param()


#    Ignore this
#    inflator = get_loyer_inflator(year)
#    simulation.inflate_survey({'loyer' : inflator})

    simulation.compute()
    simul_out_df = simulation.output_table.table
    simul_in_df = simulation.input_table.table
    print simul_out_df.loc[:,['af', 'af_base', 'af_forf', 'af_majo', 'af_nbenf']].describe()
    print 'input vars'
    print simul_in_df.columns    
    print 'output vars'
    print simul_out_df.columns
    
#     check_inputs_enumcols(simulation)
    
# Compute aggregates
    agg = Aggregates()
    agg.set_simulation(simulation)
    agg.compute()
    df1 = agg.aggr_frame
    print df1.columns
    
    print df1.to_string()
    
#    Saving aggregates
#    if writer is None:
#        writer = ExcelWriter(str(fname)
#    agg.aggr_frame.to_excel(writer, yr, index= False, header= True)


# Displaying a pivot table    
    from src.plugins.survey.distribution import OpenfiscaPivotTable
    pivot_table = OpenfiscaPivotTable()
    pivot_table.set_simulation(simulation)
    df2 = pivot_table.get_table(by ='so', vars=['nivvie']) 
    print df2.to_string()
    return df1
    
def vars_matching_entity_from_table(table, simulation=None, entity='ind'):
    """
    Extract simulation input variables which entity attribute matches entity
    from table 
    """
    vars_matching_entity = []
    for var in simulation.input_var_list:  
        if var in table.columns:
            col = simulation.get_col(var)
            if col.entity == entity:
                vars_matching_entity.append(str(var))
    return vars_matching_entity



def convert_to_3_tables(year=2006):
    survey_filename = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test.h5')
    filename3 = os.path.join(SRC_PATH, 'countries', country, 'data', 'sources', 'test3.h5')
    store = HDFStore(survey_filename)
    print store
    
    output = HDFStore(filename3)
    
    from src.lib.simulation import SurveySimulation
    simulation = SurveySimulation()
    simulation.set_config(country="france", year=year)

    
    table1 = store['survey_'+str(year)]   
    print table1
    

    for entity in ['ind','foy','men','fam']:
        key = 'survey_'+str(year) + '/'+str(entity)
        
        vars_matching_entity = vars_matching_entity_from_table(table1, simulation, entity)
        print entity, vars_matching_entity_from_table
        if entity == 'ind': 
            table_entity = table1[vars_matching_entity]
        # we take care have all ident and selecting qui==0
        else:   
            enum = 'qui'+entity
            table_entity = table1.ix[table1[enum] ==0 ,['noi','idmen','idfoy','idfam'] + 
                                                        vars_matching_entity]
            table_entity= table_entity.rename_axis(table_entity['id'+entity], axis=1)
        print key
        output.put(key, table_entity)
    
    del table1
    import gc
    gc.collect()

    store.close()
    output.close()
            
def test_laurence():
    import gc
    def reshape_tables(dfs, dfs_erf):
        agg = Aggregates()
        agg.set_header_labels() # We need this for the columns labels to work
        
        # Resetting index to avoid later trouble on manipulation
        for d in dfs:
            d.reset_index(inplace = True)
        for d in dfs_erf:
            d.reset_index(inplace = True)
            d['Mesure'] = agg.labels['dep']
            
    #         d.set_index( agg.labels['var'], inplace = True) #, drop = True ?
#         temp = dfs[0].merge(dfs[1], on = agg.labels['var'], suffixes = ('_2006','_2007'))
#         temp = temp.merge(dfs[2], on = agg.labels['var'], suffixes = ('_2007','_2008'))
#         temp = temp.merge(dfs[3], on = agg.labels['var'], suffixes = ('_2008','_2009'))
        temp = pd.concat([dfs[0],dfs[1]], ignore_index = True)
        temp = pd.concat([temp,dfs[2]], ignore_index = True)
        temp = pd.concat([temp,dfs[3]], ignore_index = True)
        
        # We split the real aggregates from the of table
        temp2 = temp[[agg.labels['var'], agg.labels['benef_real'], agg.labels['dep_real'], 'year']]
        del temp[agg.labels['benef_real']], temp[agg.labels['dep_real']]
        temp['source'] = 'of'
        temp2['source'] = 'reel'
        temp2.rename(columns = {agg.labels['benef_real'] : agg.labels['benef'],
                                agg.labels['dep_real'] : agg.labels['dep']}, 
                     inplace = True)
        temp = pd.concat([temp,temp2], ignore_index = True)
        
        temp3 = pd.concat([dfs_erf[0], dfs_erf[1]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[2]], ignore_index = True)
        temp3 = pd.concat([temp3, dfs_erf[3]], ignore_index = True)
        temp3.rename(columns = var2label, inplace = True)
        temp3 = temp3.T
        temp3.reset_index(inplace = True)
        temp3.rename(columns = {'1' : agg.labels['var'], '2' : agg.labels['dep']}, inplace = True)
        temp3['source'] = 'erfs'
        
        temp = pd.concat([temp, temp3], ignore_index = True)
#         temp.set_index(agg.labels['var'], inplace = True, drop = False)
        print temp.to_string()
        
        # Index manipulation to reshape the output
        temp.reset_index(drop = True, inplace = True)
#         index = pd.MultiIndex.from_arrays([temp['Mesure'], temp['source'], temp['year']])
        temp.set_index('Mesure', drop = True, inplace = True)
        temp.set_index('source', drop = True, append = True, inplace = True)
        temp.set_index('year', drop = True, append = True, inplace = True)
        print isinstance(temp, pd.DataFrame)
#         temp = temp.pivot(columns = 'year')
        temp = temp.unstack('year')
        print temp.to_string()
#         temp = temp.stack(agg.labels['var'], dropna = False)
        temp.fillna(0, inplace = True)
        return temp

    def save_as_xls(df):
        stxl = XLtable(df)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('resultatstest')
        erfxcel = stxl.place_table(ws)
        wb.save("C:\outputtest.xls")

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
        dfs.append(df)
        variables = agg.varlist
        del simulation, agg, label2var, var2enum
        
        #Getting ERF aggregates from ERF table
        dfs_erf.append(build_erf_aggregates(variables=variables, year= year))
        (dfs_erf[i - 2006])['year'] = year
        gc.collect()

    datatest = reshape_tables(dfs, dfs_erf)
    save_as_xls(datatest)
       
        
if __name__ == '__main__':
#     survey_case(year = 2006)
#     convert_to_3_tables()
    test_laurence()
#     year = 2006
#     dfs_erf = build_erf_aggregates(variables =["af"], year=year)
# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division
import numpy as np
from pandas import DataFrame, merge
import os 
from PyQt4.QtGui import (QWidget, QDockWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSortFilterProxyModel,
                         QSpacerItem, QSizePolicy, QApplication, QCursor, QPushButton, QInputDialog)
from PyQt4.QtCore import SIGNAL, Qt
from Config import CONF
from core.qthelpers import OfSs, DataFrameViewWidget
from core.qthelpers import MyComboBox
from core.columns import EnumCol

    
class DistributionWidget(QDockWidget):
    def __init__(self, parent = None):
        super(DistributionWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Distribution")
        self.setWindowTitle("Distribution")
        self.dockWidgetContents = QWidget()
        
        

        self.distribution_combo = MyComboBox(self.dockWidgetContents, u"Distribution de l'impact par")
        self.distribution_combo.box.setSizeAdjustPolicy(self.distribution_combo.box.AdjustToContents)
        self.distribution_combo.box.setDisabled(True)
        
        # To enable sorting of the combobox
        # hints from here: http://www.qtcentre.org/threads/3741-How-to-sort-a-QComboBox-in-Qt4
        #        and here: http://www.pyside.org/docs/pyside/PySide/QtGui/QSortFilterProxyModel.html      
        proxy = QSortFilterProxyModel(self.distribution_combo.box)
        proxy.setSourceModel(self.distribution_combo.box.model())
        self.distribution_combo.box.model().setParent(proxy)
        self.distribution_combo.box.setModel(proxy)
        
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        distribLayout = QHBoxLayout()
        distribLayout.addWidget(self.distribution_combo)
        distribLayout.addItem(spacerItem)

        self.distribution_view = DataFrameViewWidget(self.dockWidgetContents)
        self.add_btn = QPushButton(u"Ajouter variable",self.dockWidgetContents)        
        self.remove_btn = QPushButton(u"Retirer variable",self.dockWidgetContents)
        varLayout = QHBoxLayout()
        varLayout.addWidget(self.add_btn)
        varLayout.addWidget(self.remove_btn)
                
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addLayout(distribLayout)
        verticalLayout.addWidget(self.distribution_view)
        verticalLayout.addLayout(varLayout)
        
        
#        self.cols = []
        
        self.setWidget(self.dockWidgetContents)

        self.connect(self.add_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(self.remove_btn, SIGNAL('clicked()'), self.remove_var)

                
        # Initialize attributes
        self.parent = parent
         
        self.selected_vars = set(['revdisp', 'nivvie'])
        
        
        self.data = DataFrame() # Pandas DataFrame
        self.data_default = None
        
        # List of variable entering the level 0 (rows) index
        self.row_index = None
        
        # Dict of variables in the level 1 (columns)
        # exemple { revdisp : { data : [ 'current', 'default'], transform : ['mean', 'median'],  diff: ['absolute', 'relative', 'winners', 'loosers']
        
         
        
        

    @property
    def vars(self):
        return set(self.data.columns)

    def add_var(self):
        var = self.ask()
        if var is not None:
            self.selected_vars.add(var)
            self.update_view(self.data)
        else:
            return
    
    def remove_var(self):
        var = self.ask(remove=True)
        if var is not None:
            self.selected_vars.remove(var)
            self.update_view(self.data)
        else:
            return

    def ask(self, remove=False):
        if not remove:
            label = "Ajouter une variable"
            choices = self.vars - self.selected_vars
        else:
            choices =  self.selected_vars
            label = "Retirer une variable"
            
        var, ok = QInputDialog.getItem(self, label , "Choisir la variable", 
                                       sorted(list(choices)))
        if ok and var in list(choices): 
            return str(var)
        else:
            return None 

    def dist_by_changed(self):    
        widget = self.distribution_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())
            by_var = unicode(data.toString())
            self.distribution_by_var = by_var                
            self.update_view(self.data)
    
    def set_data(self, output_data, default=None):
        self.data = output_data
        if default is not None:
            self.data_default = default
        self.wght = self.data['wprm']
                 
    def set_distribution_choices(self, descriptions):
        '''
        Set the variables appearing in the ComboBox 
        '''
        combobox = self.distribution_combo.box
        combobox.setEnabled(True)
        self.disconnect(combobox, SIGNAL('currentIndexChanged(int)'), self.dist_by_changed)
         
        output_data_vars = set(self.data.columns)
        self.distribution_combo.box.clear()
        label2var = {}
        var2label = {}
        var2enum = {}
        
        for description in descriptions:    
            for var in description.col_names:
                varcol  = description.get_col(var)
                if isinstance(varcol, EnumCol):
                    var2enum[var] = varcol.enum
                        
                    if varcol.label:
                        label2var[varcol.label] = var
                        var2label[var]          = varcol.label
                        
                    else:
                        label2var[var] = var
                        var2label[var] = var
                    
                else:
                    var2enum[var] = None

        for var in set(label2var.values()).intersection(output_data_vars):
            combobox.addItem(var2label[var], var )

        self.var2label = var2label
        self.var2enum  = var2enum
        if hasattr(self, 'distribution_by_var'):
            index = combobox.findData(self.distribution_by_var)
            if index != -1:
                combobox.setCurrentIndex(index)
        self.connect(self.distribution_combo.box, SIGNAL('currentIndexChanged(int)'), self.dist_by_changed)
        self.distribution_combo.box.model().sort(0)

    def update_view(self, output_data, descriptions = None, default = None):
        '''
        Update distribution view
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        if output_data is None:
            return
        
        self.set_data(output_data, default)        
        if descriptions is not None:  
            self.set_distribution_choices(descriptions)
            
        if not hasattr(self, 'distribution_by_var'):
            self.distribution_by_var = 'so'    #TODO remove from here
        
        frame = self.updated_frame()
        self.distribution_view.set_dataframe(frame)
        self.distribution_view.reset()

        self.calculated()
        QApplication.restoreOverrideCursor()

                
    def updated_frame(self):
        '''
        Updated frame
        '''
        by_var = self.distribution_by_var
        dist_frame_dict = self.group_by(self.selected_vars, by_var)
        
        frame = None
        for dist_frame in dist_frame_dict.itervalues():
            if frame is None:
                frame = dist_frame.copy()
            else:
                dist_frame.pop('wprm')
                frame = merge(frame, dist_frame, on=by_var)
                
        by_var_label = self.var2label[by_var]
        if by_var_label == by_var:
            by_var_label = by_var + str("XX") # TODO  problem with labels from Prestation
        enum = self.var2enum[by_var]                
        
        frame = frame.reset_index(drop=True)
        
        frame.insert(0,by_var_label,u"") 
        if enum is None:
            frame[by_var_label] = frame[by_var]
        else:
            frame[by_var_label] = frame[by_var].apply(lambda x: enum._vars[x])
        frame.pop(by_var)
            
        return frame
        
    def calculated(self):
        '''
        Emits signal indicating that aggregates are computed
        '''
        self.emit(SIGNAL('calculated()'))
                
    
    
    def group_by2(self, varlist, category):
        '''
        Computes grouped aggregates
        '''
        datasets = {'data': self.data}
        aggr_dict = {}
    
        if self.data_default is not None:
            datasets['default'] = self.data_default
            
        cols = self.cols
        # cols = []

        for name, data in datasets.iteritems():
            # Computes aggregates by category
            keep = [category, 'wprm', 'champm'] + cols
            temp_data = data[keep].copy()
            temp_data['wprm'] = temp_data['wprm']*temp_data['champm']
            keep.remove('champm')
            del keep['champm']
            temp = []
            for var in varlist:
                temp_data[var] = temp_data['wprm']*data[var]
                temp.append(var)
                keep.append(var)
                    
            from pandas import pivot_table
            aggr_dict[name] = pivot_table(temp_data[keep], cols = cols,
                                  rows = category, values=keep, aggfunc = np.sum)
            
            for cat, df in aggr_dict[name].iterrows():
                for varname in varlist:
                    if name=='default':
                        label = varname + '__init'
                        df[label] = df[varname]/df['wprm']
                        del df[varname]
                    else:
                        df[varname] = df[varname]/df['wprm']
            
            print aggr_dict[name]      
            aggr_dict[name].index.names[0] = 'variable'
            aggr_dict[name] = aggr_dict[name].reset_index().unstack(cols.insert(0, 'variable'))

            
        return aggr_dict

    def group_by(self, varlist, category):
        '''
        Computes grouped aggregates
        '''
        datasets = {'data': self.data}
        aggr_dict = {}
        if self.data_default is not None:
            datasets['default'] = self.data_default

        for name, data in datasets.iteritems():
            # Computes aggregates by category
            keep = [category, 'wprm', 'champm'] 
            temp_data = data[keep].copy()
            temp_data['wprm'] = temp_data['wprm']*temp_data['champm']
            keep.remove('champm')
            del temp_data['champm']
            temp = []
            for var in varlist:
                temp_data[var] = temp_data['wprm']*data[var]
                temp.append(var)
                keep.append(var)
                
            
            grouped = temp_data[keep].groupby(category, as_index = False)
            aggr_dict[name] = grouped.aggregate(np.sum)

            # Normalizing to have the average
            for varname in temp:
                if name=='default':
                    label = varname + '__init'
                    aggr_dict[name][label] = aggr_dict[name][varname]/aggr_dict[name]['wprm']
                    del aggr_dict[name][varname]
                else:
                    aggr_dict[name][varname] = aggr_dict[name][varname]/aggr_dict[name]['wprm']
                              
        return aggr_dict


    def clear(self):
        self.aggregate_view.clear()
        self.distribution_view.clear()
        self.data = None
        self.wght = None
            
    def load_amounts_from_file(self, filenames=None, year=None):
        '''
        Loads totals from files
        '''
        from pandas import HDFStore
        if year is None:
            year     = CONF.get('simulation','datesim').year
        if filenames is None:
            data_dir = CONF.get('paths', 'data_dir')

        filename = os.path.join(data_dir, "amounts.h5")
        store = HDFStore(filename)
        df = store['amounts']            
        self.totals_df = DataFrame(data = { "amount" : df[year]  } )



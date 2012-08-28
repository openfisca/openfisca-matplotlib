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

import numpy as np
from pandas import DataFrame, read_csv
import os 
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QSortFilterProxyModel,
                         QSpacerItem, QSizePolicy, QApplication, QCursor, QPushButton, QInputDialog)
from PyQt4.QtCore import SIGNAL, Qt
from Config import CONF
from core.qthelpers import OfSs, DataFrameViewWidget
from core.qthelpers import MyComboBox
from core.columns import EnumCol, EnumPresta

class DataFrameDock(QDockWidget):
    def __init__(self, parent = None):
        super(DataFrameDock, self).__init__(parent)
        self.view = DataFrameViewWidget(self)
        self.setWindowTitle("Data")
        self.setObjectName("Data")
        dockWidgetContents = QWidget()
        verticalLayout = QVBoxLayout(dockWidgetContents)
        verticalLayout.addWidget(self.view)
        self.setWidget(dockWidgetContents)
        
    def set_dataframe(self, dataframe):
        self.view.set_dataframe(dataframe)
    
    def clear(self):
        self.view.clear()
    
class AggregateOutputWidget(QDockWidget):
    def __init__(self, parent = None):
        super(AggregateOutputWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Aggregate_Output")
        self.setWindowTitle("Aggregate_Output")
        self.dockWidgetContents = QWidget()
        
        agg_label = QLabel(u"Résultat aggrégé de la simulation", self.dockWidgetContents)

        self.totals_df = None
        
        self.aggregate_view = DataFrameViewWidget(self.dockWidgetContents)

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
        verticalLayout.addWidget(agg_label)
        verticalLayout.addWidget(self.aggregate_view)
        verticalLayout.addLayout(distribLayout)
        verticalLayout.addWidget(self.distribution_view)
        verticalLayout.addLayout(varLayout)
        
        self.setWidget(self.dockWidgetContents)

        self.connect(self.add_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(self.remove_btn, SIGNAL('clicked()'), self.remove_var)

        self.load_totals_from_file()
        
        # Initialize attributes
        self.parent = parent
        self.varlist = ['irpp', 'ppe', 'af', 'cf', 'ars', 'aeeh', 'asf', 'aspa', 'aah', 'caah', 'rsa', 'aefa', 'api', 'logt']
         
        self.selected_vars = set(['revdisp', 'nivvie'])
        
        
        self.data = DataFrame() # Pandas DataFrame

    @property
    def vars(self):
        return set(self.data.columns)

    def add_var(self):
        var = self.ask()
        if var is not None:
            self.selected_vars.add(var)
            self.update_output(self.data)
        else:
            return
    
    def remove_var(self):
        var = self.ask(remove=True)
        if var is not None:
            self.selected_vars.remove(var)
            self.update_output(self.data)
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
            self.update_output(self.data)
    
    def set_data(self, output_data):
        self.data = output_data
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
#                    if var == 'decile':
#                        print varcol.__dict__
                        
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

    def update_output(self, output_data, descriptions = None):
        '''
        Update aggregate outputs and (re)set views # TODO we may split this for the two views 
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        if output_data is None:
            return
        self.set_data(output_data)        
        
        if descriptions is not None:  
            self.set_distribution_choices(descriptions)
            
        if not hasattr(self, 'distribution_by_var'):
            self.distribution_by_var = 'typmen15'
        
        by_var = self.distribution_by_var
        

        V = []
        M = []
        B = []
        T = []            # Totals de l'année 
        for var in self.varlist:
            montant, benef = self.get_aggregate(var)
            V.append(var)
            M.append(montant)
            B.append(benef)
            if var in self.totals_df.index:
                T.append(self.totals_df.get_value(var, "total"))
            else:
                T.append("n.d.")
        
        
        items = [(u'Mesure', V), 
                 (u"Dépense\n(millions d'€)", M), 
                 (u"Bénéficiaires\n(milliers de ménages)", B)]
        
        if True:
            items.append((u"Dépenses réelles\n(millions d'€)", T))
        
        aggr_frame = DataFrame.from_items(items)
        self.aggregate_view.set_dataframe(aggr_frame)

        dist_frame = self.group_by(self.selected_vars, by_var)
        by_var_label = self.var2label[by_var]
        if by_var_label == by_var:
            by_var_label = by_var + str("XX") # TODO  problem with labels from Prestation
        
        dist_frame.insert(0,by_var_label,u"") 
        enum = self.var2enum[by_var]
        if enum is None:
            dist_frame[by_var_label] = dist_frame[by_var]
        else:
            dist_frame[by_var_label] = dist_frame[by_var].apply(lambda x: enum._vars[x])
            
        dist_frame.pop(by_var)
                
        self.distribution_view.set_dataframe(dist_frame)
        self.distribution_view.reset()
        self.calculated()
        QApplication.restoreOverrideCursor()
        
    def calculated(self):
        self.emit(SIGNAL('calculated()'))
                
    def get_aggregate(self, var):
        '''
        returns aggregate spending, nb of beneficiaries
        '''
        montants = self.data[var]
        beneficiaires = self.data[var].values != 0
        return int(round(sum(montants*self.wght)/10**6)), int(round(sum(beneficiaires*self.wght)/10**3))
    
    def group_by(self, varlist, category):
        keep = [category, 'wprm'] 
        
        temp_data = self.data[keep].copy()
        temp = []
        for var in varlist:
            temp_data[var] = self.wght*self.data[var]
            temp.append(var)
            keep.append(var)
        grouped = temp_data[keep].groupby(category, as_index = False)
        aggr = grouped.aggregate(np.sum)

        for varname in temp:
            aggr[varname] = aggr[varname]/aggr['wprm']
        return aggr

    def clear(self):
        self.aggregate_view.clear()
        self.distribution_view.clear()
        self.data = None
        self.wght = None
            
    def load_totals_from_file(self, filenames=None, year=None):
        '''
        Loads totals from files
        '''
        if year is None:
            year     = str(CONF.get('simulation','datesim').year)
        if filenames is None:
            data_dir = CONF.get('paths', 'data_dir')
            #fname    = CONF.get('calibration','inflation_filename')  # TODO
            fname = "totals_pfam.csv"
            filename = os.path.join(data_dir, fname)
            filenames = [filename]

        
        for fname in filenames:
            with open(fname) as f_tot:
                totals = read_csv(f_tot)
            if year in totals:
                if self.totals_df is None:
                    self.totals_df = DataFrame(data = {"var" : totals["var"],
                              "total" : totals[year]  } )
                    self.totals_df = self.totals_df.set_index("var")
            
        print self.totals_df
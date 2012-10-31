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
from pandas import DataFrame
import os 
from PyQt4.QtGui import (QWidget, QDockWidget, QVBoxLayout, QComboBox,
                         QApplication, QCursor, QInputDialog, QSizePolicy, QMenu)
from PyQt4.QtCore import SIGNAL, Qt
from Config import CONF
from core.qthelpers import OfSs, DataFrameViewWidget, create_action, add_actions

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
        self.setObjectName(u"Aggrégats")
        self.setWindowTitle(u"Aggrégats")
        self.dockWidgetContents = QWidget()
        
        self.aggregate_view = DataFrameViewWidget(self.dockWidgetContents)

        # Menu 
#        menu_bar = QMenuBar()

        self.select_menu = QMenu()
        action_real    = create_action(self, u"Réel",       toggled = self.toggle_show_real)
        action_diff    = create_action(self, u"Différence", toggled = self.toggle_show_diff)
        self.action_default = create_action(self, u"Référence",  toggled = self.toggle_show_default)
        self.actions = [action_real, action_diff]
        
        add_actions(self.select_menu, self.actions)
        
        headers = self.aggregate_view.horizontalHeader()
        self.headers = headers
        headers.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.headers,SIGNAL('customContextMenuRequested(QPoint)'), self.ctx_select_menu)
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.aggregate_view)
        self.setWidget(self.dockWidgetContents)
        
        # Initialize attributes
        self.aggr_default_frame = None
        self.totals_df = None
        self.parent = parent
        self.varlist = ['cotsoc_noncontrib', 'csg', 'crds',
                        'irpp', 'ppe',
                        'af', 'af_base', 'af_majo','af_forf', 'cf',
                        'paje_base', 'paje_nais', 'paje_colca', 'paje_clmg',
                        'ars', 'aeeh', 'asf', 'aspa',
                        'aah', 'caah', 
                        'rsa', 'rsa_act', 'aefa', 'api',
                        'logt']
         
        self.data = DataFrame()
        self.data_default = None
        self.load_amounts_from_file()
        self.aggr_frame = None
        action_real.toggle()
        action_diff.toggle()
        
        

    def ctx_select_menu(self, point):
        self.select_menu.exec_( self.headers.mapToGlobal(point) )
        

    def toggle_show_default(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_default = boolean
        if self.aggr_frame is not None:
            self.update_view()


    def toggle_show_real(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_real = boolean
        if self.aggr_frame is not None:
            self.update_view()
            
    def toggle_show_diff(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_diff = boolean
        if boolean is True:
            self.show_real = True 
        if self.aggr_frame is not None:
            self.update_view()

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
    
    def set_data(self, output_data, default=None):
        self.data = output_data
        if default is not None:
            self.data_default = default
        self.wght = self.data['wprm']
                 

    def update_output(self, output_data, descriptions = None, default = None):
        '''
        Update aggregate outputs and reset view
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        if output_data is None:
            return
        
        if descriptions is not None:
            self.description = descriptions[1]
        
        if default is not None:
            if self.action_default not in self.actions:
                self.actions.append(self.action_default)
                add_actions(self.select_menu, self.actions)
            self.action_default.toggle()
        else:
            self.show_default = False 
            if self.action_default in self.actions:
                self.actions.remove(self.action_default)
                add_actions(self.select_menu, self.actions)
        
        self.set_data(output_data, default)        
        self.compute_aggregates()
        self.update_view()
        self.calculated()
        QApplication.restoreOverrideCursor()


    def compute_aggregates(self):
        '''
        Compute aggregate amounts
        '''
        V  = []    
        M = {'data': [], 'default': []}
        B = {'data': [], 'default': []}
        U = []
        M_label = {'data': u"Dépense\n(millions d'€)", 
                   'default': u"Dépense initiale\n(millions d'€)"}
        B_label = {'data': u"Bénéficiaires\n(en milliers)", 
                   'default': u"Bénéficiaires\ninitiaux\n(en milliers)"}
        
        for var in self.varlist:
            # totals from current data and default data if exists
            montant_benef = self.get_aggregate(var)
            V.append(var)
                        
            try:
                varcol  = self.description.get_col(var)
                unit = varcol._unit
            except:
                unit = 'NA'
                 
            U.append(unit)
            for dataname in montant_benef:
                M[dataname].append( montant_benef[dataname][0] )
                B[dataname].append( montant_benef[dataname][1] )
        
        # build items list
        items = [(u'Mesure', V)]

        for dataname in M:
            if M[dataname]:
                items.append( (M_label[dataname], M[dataname]))
                items.append(  (B_label[dataname], B[dataname]) )

        items.append( (u"Unité", U) )        
        self.aggr_frame = DataFrame.from_items(items)

    def add_real(self):
        '''
        Adds administrative data to dataframe
        '''
        if u"Dépenses\nréelles\n(millions d'€)" not in self.aggr_frame:
            T = []
            for var in self.varlist:
                # totals from administrative data        
                if var in self.totals_df.index:
                    T.append(self.totals_df.get_value(var, "amount"))
                else:
                    T.append("n.d.")

            self.aggr_frame[u"Dépenses\nréelles\n(millions d'€)"] = T
        

    def rmv_real(self):
        '''
        Removes administrative data from dataframe
        '''
        if u"Dépenses\nréelles\n(millions d'€)" in self.aggr_frame.columns:
            self.aggr_frame = self.aggr_frame.drop([u"Dépenses\nréelles\n(millions d'€)"], axis =1)
        self.rmv_diff()
        
    def add_diff(self):
        '''
        Computes and adds relative differences
        '''
        from numpy import nan         
        if self.show_real:
            dep = self.aggr_frame[u"Dépense\n(millions d'€)"]
            ref_dep = self.aggr_frame[u"Dépenses\nréelles\n(millions d'€)"]
            ref_dep2 = ref_dep.copy() 
            ref_dep2[(ref_dep=="n.d.")] = nan   
            self.aggr_frame[u"Différence\nrelative"] = (dep-ref_dep2)/abs(ref_dep2)
        elif self.show_default:
            dep = self.aggr_frame[u"Dépense\n(millions d'€)"]
            ref_dep = self.aggr_frame[u"Dépense initiale\n(millions d'€)"]
            self.aggr_frame[u"Différence\nrelative"] = (dep-ref_dep)/abs(ref_dep)
            
    def rmv_diff(self):
        '''
        Removes relative differences
        '''
        if u"Différence\nrelative" in self.aggr_frame.columns:
            self.aggr_frame = self.aggr_frame.drop([u"Différence\nrelative"], axis =1)

    def add_default(self):
        '''
        Adds default aggregates when in reform mode
        '''
        default_cols = [u"Dépense initiale\n(millions d'€)", u"Bénéficiaires\ninitiaux\n(en milliers)"]
        if self.aggr_default_frame is not None:
            self.aggr_frame[default_cols] = self.aggr_default_frame[default_cols] 
        
    def rmv_default(self):
        '''
        Removes default aggregates when in reform mode
        '''
        default_cols = [u"Dépense initiale\n(millions d'€)", u"Bénéficiaires\ninitiaux\n(en milliers)"]
        if default_cols[0] in self.aggr_frame:
            self.aggr_default_frame = self.aggr_frame[ default_cols ]
            self.aggr_frame = self.aggr_frame.drop(default_cols, axis=1)
        
    def update_view(self):
        '''
        Update aggregate amounts view
        '''
        if self.show_real:
            self.add_real()
            if self.show_diff:
                self.add_diff()
            else:
                self.rmv_diff()
        else:
            self.rmv_real()
            
            
        if self.show_default:
            self.add_default()
            if self.show_diff:
                self.add_diff()
            else:
                self.rmv_diff()
        else:
            self.rmv_default()
            
        self.aggregate_view.set_dataframe(self.aggr_frame)
        self.aggregate_view.resizeColumnsToContents()
        self.aggregate_view.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
                
    def calculated(self):
        '''
        Emits signal indicating that aggregates are computed
        '''
        self.emit(SIGNAL('calculated()'))
                
    def get_aggregate(self, var):
        '''
        Returns aggregate spending, nb of beneficiaries
        '''
        datasets = {'data': self.data}
        m_b = {}
        
        if self.data_default is not None:
            datasets['default'] = self.data_default

        for name, data in datasets.iteritems():
            montants = data[var]
            beneficiaires = data[var].values != 0
            m_b[name] = [int(round(sum(montants*self.wght)/10**6)),
                        int(round(sum(beneficiaires*self.wght)/10**3))]
        return m_b
    
    
    def clear(self):
        self.aggr_default_frame = None
        self.aggregate_view.clear()
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



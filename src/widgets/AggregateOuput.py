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
from PyQt4.QtGui import (QWidget, QDockWidget, QVBoxLayout,
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

        # Context Menu         
        headers = self.aggregate_view.horizontalHeader()
        self.headers = headers
        headers.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.headers,SIGNAL('customContextMenuRequested(QPoint)'), self.ctx_select_menu)
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.aggregate_view)
        self.setWidget(self.dockWidgetContents)
        
        # Initialize attributes

        self.parent = parent
        self.varlist = ['cotsoc_noncontrib', 'csg', 'crds',
                        'irpp', 'ppe',
                        'af', 'af_base', 'af_majo','af_forf', 'cf',
                        'paje_base', 'paje_nais', 'paje_colca', 'paje_clmg',
                        'ars', 'aeeh', 'asf', 'aspa',
                        'aah', 'caah', 
                        'rsa', 'rsa_act', 'aefa', 'api',
                        'logt', 'alf', 'als', 'apl']
         
        self.data = DataFrame()
        self.data_default = None
        self.aggr_frame = None
        self.aggr_default_frame = None
        self.totals_df = None
        self.load_amounts_from_file()
        
        self.set_header_labels()


    def set_header_labels(self):
        '''
        Sets headers labels
        '''
        
        self.dep_label           = u"Dépense\n(millions d'€)" 
        self.benef_label         = u"Bénéficiaires\n(milliers)"
        self.dep_default_label   = u"Dépense initiale\n(millions d'€)"
        self.benef_default_label = u"Bénéficiaires\ninitiaux\n(milliers)"
        self.dep_real_label      = u"Dépenses\nréelles\n(millions d'€)"
        self.benef_real_label    = u"Bénéficiaires\nréels\n(milliers)"
        self.dep_diff_label      = u"Diff.relative\nDépenses"
        self.benef_diff_label    = u"Diff.relative\nBénéficiaires"

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

        self.select_menu = QMenu()
        action_real    = create_action(self, u"Réel",       toggled = self.toggle_show_real)
        action_diff    = create_action(self, u"Différence", toggled = self.toggle_show_diff)
        action_default = create_action(self, u"Référence",  toggled = self.toggle_show_default)
                
        if default is None:
            self.show_default = False
            if self.totals_df is not None:
                add_actions(self.select_menu, [action_real, action_diff])
                action_diff.toggle()
                action_real.toggle()
            else: 
                add_actions(self.select_menu, [])
                self.show_real = False
                self.show_diff = False
        else:
            self.show_real = False
            add_actions(self.select_menu, [action_default, action_diff])
            action_diff.toggle()
            action_default.toggle() 
            
        
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

        M_label = {'data': self.dep_label, 
                   'default': self.dep_default_label}
        B_label = {'data': self.benef_label, 
                   'default': self.benef_default_label}

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
        if (self.dep_real_label not in self.aggr_frame) and (self.totals_df is not None) :
            A, B = [], []
            for var in self.varlist:
                # totals from administrative data        
                if var in self.totals_df.index:
                    A.append(self.totals_df.get_value(var, "amount"))
                    B.append(self.totals_df.get_value(var, "benef"))
                else:
                    A.append("n.d.")
                    B.append("n.d.")

            self.aggr_frame[self.dep_real_label] = A
            self.aggr_frame[self.benef_real_label] = B

    def rmv_real(self):
        '''
        Removes administrative data from dataframe
        '''
        if self.dep_real_label in self.aggr_frame.columns:
            self.aggr_frame = self.aggr_frame.drop([self.dep_real_label], axis =1)
        self.rmv_diff()
        
    def add_diff(self):
        '''
        Computes and adds relative differences
        '''
        from numpy import nan         
        dep   = self.aggr_frame[self.dep_label]
        benef = self.aggr_frame[self.benef_label]
        if self.show_real:
            ref_dep_label, ref_benef_label = self.dep_real_label, self.benef_real_label
        elif self.show_default:
            ref_dep_label, ref_benef_label = self.dep_default_label, self.benef_default_label
            
        ref_dep0 = self.aggr_frame[ref_dep_label]
        ref_dep = ref_dep0.copy() 
        ref_dep[(ref_dep=="n.d.")] = nan   
        ref_benef0 = self.aggr_frame[ref_benef_label]
        ref_benef = ref_benef0.copy() 
        ref_benef[(ref_benef=="n.d.")] = nan
                    
        self.aggr_frame[self.dep_diff_label] = (dep-ref_dep)/abs(ref_dep)
        self.aggr_frame[self.benef_diff_label] = (benef-ref_benef)/abs(ref_benef)
            
    def rmv_diff(self):
        '''
        Removes relative differences
        '''
        if self.dep_diff_label in self.aggr_frame.columns:
            self.aggr_frame = self.aggr_frame.drop([self.dep_diff_label, self.benef_diff_label], axis =1)

    def add_default(self):
        '''
        Adds default aggregates when in reform mode
        '''
        default_cols = [self.dep_default_label, self.benef_default_label]
        if self.aggr_default_frame is not None:
            self.aggr_frame[default_cols] = self.aggr_default_frame[default_cols] 
        
    def rmv_default(self):
        '''
        Removes default aggregates when in reform mode
        '''
        default_cols = [self.dep_default_label, self.benef_default_label]
        if default_cols[0] in self.aggr_frame:
            self.aggr_default_frame = self.aggr_frame[ default_cols ]
            self.aggr_frame = self.aggr_frame.drop(default_cols, axis=1)
        
    def update_view(self):
        '''
        Update aggregate amounts view
        '''
        if self.show_real:
            self.add_real()
        else:
            self.rmv_real()
             
        if self.show_default:
            self.add_default()
        else:
            self.rmv_default()
            
        if self.show_diff:
            self.add_diff()
        else:
            self.rmv_diff()
            
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
        print store
        df_a = store['amounts']
        df_b = store['benef']
        try:
            self.totals_df = DataFrame(data = { "amount" : df_a[year]/10**6, "benef": df_b[year]/1000 } )
            print self.totals_df.to_string()
        except:
#            raise Exception(" No administrative data available for year " + str(year))
            print " No administrative data available for year " + str(year)
            self.totals_df = None
            pass
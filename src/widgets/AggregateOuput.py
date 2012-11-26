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
from numpy import nan         
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
        self.var_label           = u"Mesure"
        self.unit_label          = u"Unité"
        self.dep_label           = u"Dépense\n(millions d'€)" 
        self.benef_label         = u"Bénéficiaires\n(milliers)"
        self.dep_default_label   = u"Dépense initiale\n(millions d'€)"
        self.benef_default_label = u"Bénéficiaires\ninitiaux\n(milliers)"
        self.dep_real_label      = u"Dépenses\nréelles\n(millions d'€)"
        self.benef_real_label    = u"Bénéficiaires\nréels\n(milliers)"
        self.dep_diff_abs_label      = u"Diff. absolue\nDépenses\n(millions d'€) "
        self.benef_diff_abs_label    = u"Diff absolue\nBénéficiaires\n(milliers)"
        self.dep_diff_rel_label      = u"Diff. relative\nDépenses"
        self.benef_diff_rel_label    = u"Diff. relative\nBénéficiaires"

    def ctx_select_menu(self, point):
        self.select_menu.exec_( self.headers.mapToGlobal(point) )

    def toggle_show_default(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_default = boolean
        self.update_view()

    def toggle_show_real(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_real = boolean
        self.update_view()
            
    def toggle_show_diff_abs(self, boolean):
        ''' 
        Toggles differences 
        '''
        self.show_diff_abs = boolean
        self.update_view()

    def toggle_show_diff_rel(self, boolean):
        ''' 
        Toggles differences 
        '''
        self.show_diff_rel = boolean
        self.update_view()

    def toggle_show_dep(self, boolean):
        '''
        Toggles to show amounts (dépenses) 
        '''
        self.show_dep = boolean
        self.update_view()
        
    def toggle_show_benef(self, boolean):
        '''
        Toggles to show beneficiaries
        ''' 
        self.show_benef = boolean
        self.update_view()
        
    def set_data(self, output_data, default=None):
        '''
        Sets data and weight
        '''
        self.data = output_data
        if default is not None:
            self.data_default = default
        self.wght = self.data['wprm']
                 
    def update_output(self, output_data, descriptions = None, default = None):
        '''
        Update aggregate outputs and reset view
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        self.dont_update = True
        if output_data is None:
            return
        
        if descriptions is not None:
            self.description = descriptions[1]

        self.select_menu = QMenu()
        action_dep     = create_action(self, u"Dépenses",   toggled = self.toggle_show_dep)
        action_benef     = create_action(self, u"Bénéficiaires", toggled = self.toggle_show_benef)
        action_real    = create_action(self, u"Réel",       toggled = self.toggle_show_real)
        action_diff_abs    = create_action(self, u"Diff. absolue", toggled = self.toggle_show_diff_abs)
        action_diff_rel    = create_action(self, u"Diff. relative ", toggled = self.toggle_show_diff_rel)
        action_default = create_action(self, u"Référence",  toggled = self.toggle_show_default)
                
        actions = [action_dep, action_benef]        
        action_dep.toggle()
        action_benef.toggle()
                
        if default is None:
            self.show_default = False
            if self.totals_df is not None:
                actions.append(action_real)
                actions.append(action_diff_abs)
                actions.append(action_diff_rel)
                action_real.toggle()
                action_diff_abs.toggle()
                action_diff_rel.toggle()
            else: 
                self.show_real = False
                self.show_diff_abs = False
                self.show_diff_rel = False

        else:
            self.show_real = False
            actions.append(action_default)
            actions.append(action_diff_abs)
            actions.append(action_diff_rel)            
            action_default.toggle() 
            action_diff_abs.toggle()
            action_diff_rel.toggle()
            
        add_actions(self.select_menu, actions)
        self.set_data(output_data, default)        
        self.compute_aggregates()
        self.compute_real()
        self.dont_update = False
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

        label2var, var2label, var2enum = self.description.builds_dicts()
        for var in self.varlist:
            # amounts and beneficiaries from current data and default data if exists
            montant_benef = self.get_aggregate(var)
            V.append(var2label[var])
                        
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
        items = [(self.var_label, V)]

        for dataname in M:
            if M[dataname]:
                items.append( (M_label[dataname], M[dataname]))
                items.append(  (B_label[dataname], B[dataname]) )

        items.append( (self.unit_label, U) )        
        self.aggr_frame = DataFrame.from_items(items)

    def compute_real(self):
        '''
        Adds administrative data to dataframe
        '''
        if self.totals_df is None:
            return    
        A, B = [], []
        for var in self.varlist:
            # totals from administrative data        
            if var in self.totals_df.index:
                A.append(self.totals_df.get_value(var, "amount"))
                B.append(self.totals_df.get_value(var, "benef"))
            else:
                A.append(nan)
                B.append(nan)
        self.aggr_frame[self.dep_real_label] = A
        self.aggr_frame[self.benef_real_label] = B

        
    def compute_diff(self):
        '''
        Computes and adds relative differences
        '''
        dep   = self.aggr_frame[self.dep_label]
        benef = self.aggr_frame[self.benef_label]
        
        if self.show_default:
            ref_dep_label, ref_benef_label = self.dep_default_label, self.benef_default_label
            if ref_dep_label not in self.aggr_frame:
                return
        elif self.show_real:
            ref_dep_label, ref_benef_label = self.dep_real_label, self.benef_real_label
        else:
            return
        
        ref_dep = self.aggr_frame[ref_dep_label]   
        ref_benef = self.aggr_frame[ref_benef_label]
                    
        self.aggr_frame[self.dep_diff_rel_label] = (dep-ref_dep)/abs(ref_dep)
        self.aggr_frame[self.benef_diff_rel_label] = (benef-ref_benef)/abs(ref_benef)
        self.aggr_frame[self.dep_diff_abs_label] = (dep-ref_dep)
        self.aggr_frame[self.benef_diff_abs_label] = (benef-ref_benef)
        
        
    def add_default(self):
        '''
        Adds default aggregates when in reform mode
        '''
        default_cols = [self.dep_default_label, self.benef_default_label]
        if self.aggr_default_frame is not None:
            self.aggr_frame[default_cols] = self.aggr_default_frame[default_cols] 
        
        
    def update_view(self):
        '''
        Update aggregate amounts view
        '''
        if self.aggr_frame is None:
            return
        
        if self.dont_update:
            return
            
        cols = [self.var_label, self.unit_label,
                self.dep_label, self.dep_default_label, self.dep_real_label, 
                self.dep_diff_abs_label, self.dep_diff_rel_label, 
                self.benef_label, self.benef_default_label, self.benef_real_label,
                self.benef_diff_abs_label, self.benef_diff_rel_label]
        
        if not self.show_real:
            cols.remove(self.dep_real_label) 
            cols.remove(self.benef_real_label)

        if not self.show_default:
            cols.remove(self.dep_default_label)
            cols.remove(self.benef_default_label)
            

        remove_all_diffs =  not (self.show_real or self.show_default)
        if not remove_all_diffs:
            self.compute_diff()
        
        if (not self.show_diff_abs) or remove_all_diffs:
            cols.remove(self.dep_diff_abs_label)
            cols.remove(self.benef_diff_abs_label)    
        
        if (not self.show_diff_rel) or remove_all_diffs: 
            cols.remove(self.dep_diff_rel_label)
            cols.remove(self.benef_diff_rel_label)
 
        if not self.show_dep:
            for label in [self.dep_label, self.dep_real_label, self.dep_default_label, self.dep_diff_abs_label, self.dep_diff_rel_label]:
                if label in cols:
                    cols.remove(label)

        if not self.show_benef:
            for label in [self.benef_label, self.benef_real_label, self.benef_default_label, self.benef_diff_abs_label, self.benef_diff_rel_label]:
                if label in cols:
                    cols.remove(label)
                
        self.aggregate_view.set_dataframe(self.aggr_frame[cols])
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

        try:
            filename = os.path.join(data_dir, "amounts.h5")
            store = HDFStore(filename)
    
            df_a = store['amounts']
            df_b = store['benef']
            print df_a.to_string()
            print df_b.to_string()
            self.totals_df = DataFrame(data = { "amount" : df_a[year]/10**6, "benef": df_b[year]/1000 } )
            row = DataFrame({'amount': nan, 'benef': nan}, index = ['logt']) 
            self.totals_df = self.totals_df.append(row)

            # Add some aditionnals totals
            for col in ['amount', 'benef']:
                
                # Deals woth logt
                logt = 0
                for var in ['apl', 'alf', 'als']:
                    logt += self.totals_df.get_value(var, col)
                self.totals_df.set_value('logt', col,  logt)
                
                # Deals wit irpp, csg, crds
                for var in ['irpp', 'csg', 'crds']:
                    if col in ['amount']:
                        val = - self.totals_df.get_value(var, col)
                        self.totals_df.set_value(var, col, val)
                    
                print self.totals_df.to_string()
        except:
            raise Exception(" No administrative data available for year " + str(year))
            print " No administrative data available for year " + str(year)
            self.totals_df = None
            return
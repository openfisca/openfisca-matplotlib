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
from pandas import DataFrame
import os 
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QComboBox,
                         QApplication, QCursor, QInputDialog)
from PyQt4.QtCore import SIGNAL, Qt
from Config import CONF
from core.qthelpers import OfSs, DataFrameViewWidget

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
        
        agg_label = QLabel(u"Résultats aggrégés de la simulation", self.dockWidgetContents)

        self.totals_df = None
        
        self.aggregate_view = DataFrameViewWidget(self.dockWidgetContents)


        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(agg_label)
        verticalLayout.addWidget(self.aggregate_view)
        
        
#        self.cols = []
        
        self.setWidget(self.dockWidgetContents)


        self.load_amounts_from_file()
                
        # Initialize attributes
        self.parent = parent
        self.varlist = ['cotsoc_noncontrib', 'csg', 'crds',
                        'irpp', 'ppe',
                        'af', 'af_base', 'af_majo','af_forf', 'cf',
                        'paje_base', 'paje_nais', 'paje_colca', 'paje_clmg',
                        'ars', 'aeeh', 'asf', 'aspa',
                        'aah', 'caah', 
                        'rsa', 'rsa_act', 'aefa', 'api',
                        'logt']
         
        self.selected_vars = set(['revdisp', 'nivvie'])
        
        
        self.data = DataFrame() # Pandas DataFrame
        self.data_default = None



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
                 

    def update_output(self, output_data, default = None):
        '''
        Update aggregate outputs and reset view
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        if output_data is None:
            return
        
        self.set_data(output_data, default)        
        self.update_aggregate_view()
        self.calculated()
        QApplication.restoreOverrideCursor()


    def update_aggregate_view(self):
        '''
        Update aggregate amounts view
        '''
        V,  T  = [],  []    
        M = {'data': [], 'default': []}
        B = {'data': [], 'default': []}
        M_label = {'data': u"Dépense\n(millions d'€)", 
                   'default': u"Dépense initiale\n(millions d'€)"}
        B_label = {'data': u"Bénéficiaires\n(milliers de ménages)", 
                   'default': u"Bénéficiaires initiaux\n(milliers de ménages)"}
        
        for var in self.varlist:
            # totals from current data and default data if exists
            montant_benef = self.get_aggregate(var)
            V.append(var)
            for dataname in montant_benef:
                M[dataname].append( montant_benef[dataname][0] )
                B[dataname].append( montant_benef[dataname][1] )
            
            # totals from administrative data
            if var in self.totals_df.index:
                T.append(self.totals_df.get_value(var, "amount"))
            else:
                T.append("n.d.")
        
        # build items list
        items = [(u'Mesure', V)]
        for dataname in M:
            if M[dataname]:
                items.append( (M_label[dataname], M[dataname]))
                items.append(  (B_label[dataname], B[dataname]) )
        
        items.append((u"Dépenses réelles\n(millions d'€)", T))
        aggr_frame = DataFrame.from_items(items)
        self.aggregate_view.set_dataframe(aggr_frame)

                
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



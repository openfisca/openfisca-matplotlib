# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox,
                         QSpacerItem, QSizePolicy)
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant
from core.qthelpers import OfSs, DataFrameViewWidget
import numpy as np
from pandas import DataFrame

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
        agg_label = QLabel(u"Résultat aggregé de la simulation", self.dockWidgetContents)
        self.aggregate_view = DataFrameViewWidget(self.dockWidgetContents)

        dist_label = QLabel(u"Distribution de l'impact par", self.dockWidgetContents)
        self.distribution_combo = QComboBox(self.dockWidgetContents)
        self.distribution_combo.addItems([u'déciles', u'types de famille'])
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(dist_label)
        horizontalLayout.addWidget(self.distribution_combo)
        horizontalLayout.addItem(spacerItem)

        self.distribution_view = DataFrameViewWidget(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(agg_label)
        verticalLayout.addWidget(self.aggregate_view)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(self.distribution_view)
        self.setWidget(self.dockWidgetContents)

        # Initialize attributes
        self.parent = parent
        self.varlist = ['irpp', 'ppe', 'af', 'cf', 'ars', 'aeeh', 'asf', 'aspa', 'aah', 'caah', 'rsa', 'aefa', 'api', 'logt']
        self.data = DataFrame() # Pandas DataFrame
            
    def update_output(self, output_data):
        self.data = output_data
        self.wght = self.data['wprm']
        V = []
        M = []
        B = []
        for var in self.varlist:
            montant, benef = self.get_aggregate(var)
            V.append(var)
            M.append(montant)
            B.append(benef)
        
        items = [(u'Mesure', V), 
                 (u"Dépense\n(millions d'€)", M), 
                 (u"Bénéficiaires\n(milliers de ménages)", B)]
        aggr_frame = DataFrame.from_items(items)
        self.aggregate_view.set_dataframe(aggr_frame)

        dist_frame = self.group_by(['revdisp', 'nivvie'], 'typ_men')
        self.distribution_view.set_dataframe(dist_frame)
        
    def get_aggregate(self, var):
        '''
        returns aggregate spending, nb of beneficiaries
        '''
        montants = self.data[var]
        beneficiaires = self.data[var].values != 0
        return int(round(sum(montants*self.wght)/10**6)), int(round(sum(beneficiaires*self.wght)/10**3))
    
    def group_by(self, varlist, category):
        keep = [category, 'wprm']
        temp = []
        for var in varlist:
            self.data['__' + var] = self.wght*self.data[var]
            temp.append('__'+var)
            keep.append('__'+var)
        grouped = self.data[keep].groupby(category, as_index = False)
        aggr = grouped.aggregate(np.sum)
        total = self.data[keep].sum()

        for varname in temp:
            aggr[varname] = aggr[varname]/aggr['wprm']
            total[varname] = total[varname]/total['wprm']
        
        return aggr

    def clear(self):
        self.aggregate_view.clear()
        self.distribution_view.clear()
        self.data = None
        self.wght = None
            

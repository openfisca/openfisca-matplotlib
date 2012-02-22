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
from core.qthelpers import OfTableView

class AggregateOutputWidget(QDockWidget):
    def __init__(self, parent = None):
        super(AggregateOutputWidget, self).__init__(parent)
        
        # Create geometry
        self.setObjectName("Aggregate_Output")
        self.setWindowTitle("Aggregate_Output")
        self.dockWidgetContents = QWidget()
        agg_label = QLabel(u"Résultat aggregé de la simulation", self.dockWidgetContents)
        self.aggregate_view = OfTableView(self.dockWidgetContents)

        dist_label = QLabel(u"Distribution de l'impact par", self.dockWidgetContents)
        self.distribution_combo = QComboBox(self.dockWidgetContents)
        self.distribution_combo.addItems([u'déciles', u'types de famille'])
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(dist_label)
        horizontalLayout.addWidget(self.distribution_combo)
        horizontalLayout.addItem(spacerItem)

        self.distribution_view = OfTableView(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(agg_label)
        verticalLayout.addWidget(self.aggregate_view)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(self.distribution_view)
        self.setWidget(self.dockWidgetContents)

        self.parent = parent
        self.varlist = ['irpp', 'af', 'cf', 'ars', 'logt']
        
    def set_modeldata(self, datatable):
        self.aggregate_model = AggregateModel(datatable, self)
        self.aggregate_view.setModel(self.aggregate_model)
        self.distribution_model = DistributionModel(datatable, self)
        self.distribution_view.setModel(self.distribution_model)
    
    def update_output(self, output_data):
        self.data = output_data
        self.weights = self.data['wprm'].vals
        self.totaux = []
        for var in self.varlist:
            self.totaux.append((var, self.get_aggregate(var)))
        self.set_modeldata(self.totaux)

    def get_aggregate(self, var):
        return float(sum(self.data[var].vals*self.weights))/10**6
    
class AggregateModel(QAbstractTableModel):
    def __init__(self, datatable, parent=None):
        super(AggregateModel, self).__init__(parent)
        self.datatable = datatable
    
    def rowCount(self, parent):
        return len(self.datatable)

    def columnCount(self, parent):
        return 2
    
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None
        col = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            return QVariant(self.datatable[row][col])
        if role == Qt.TextAlignmentRole:
            if col == 1: return Qt.AlignRight
        return QVariant()
        
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section ==0: return u'Mesure'
                elif section == 1: return u"Dépense\n(millions d'€)"
        return QVariant()
    
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
class DistributionModel(QAbstractTableModel):
    def __init__(self, datatable, parent=None):
        super(DistributionModel, self).__init__(parent)
        self.datatable = datatable
    
    def rowCount(self, parent):
        return 4

    def columnCount(self, parent):
        return 4
    
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None
        col = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return QVariant()
    
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    

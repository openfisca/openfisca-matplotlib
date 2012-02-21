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
from PyQt4.QtGui import QDockWidget
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant
from views.ui_aggregate_output import Ui_Aggregate_Output


class AggregateOutputWidget(QDockWidget, Ui_Aggregate_Output):
    def __init__(self, parent = None):
        super(AggregateOutputWidget, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent

    def set_datatable(self, datatable):
        self.data = datatable
        self.aggregate_model = AggregateModel(datatable, self)
        self.aggregate_view.setModel(self.aggregate_model)
        self.distribution_model = DistributionModel(datatable, self)
        self.distribution_view.setModel(self.distribution_view)
                
class AggregateModel(QAbstractTableModel):
    def __init__(self, datatable, parent=None):
        super(AggregateModel, self).__init(parent)
        self.data = datatable
    
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
    
class DistributionModel(QAbstractTableModel):
    def __init__(self, datatable, parent=None):
        super(DistributionModel, self).__init(parent)
        self.data = datatable
    
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

    

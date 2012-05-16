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
                         QSpacerItem, QSizePolicy, QApplication, QCursor)
from PyQt4.QtCore import SIGNAL, Qt, QString
from core.qthelpers import OfSs, DataFrameViewWidget
import numpy as np
from pandas import DataFrame
from Calibration import MyComboBox
from core.columns import BoolCol, AgesCol, EnumCol
try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

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

        self.distribution_by_var = 'typ_men'
#        self.distribution_by_var_dict = {}
#        distribution_choices = [(u'déciles', 'decile'),
#                                (u'types de famille', 'typ_men'),
#                                (u'so', 'so'),
#                                (u'typmen15', 'typmen15'),
#                                (u'tu99', 'tu99')]
        self.distribution_choices = []
        self.distribution_combo = MyComboBox(self.dockWidgetContents, u"Distribution de l'impact par", self.distribution_choices)
        self.distribution_combo.box.setDisabled(True)
        
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        horizontalLayout = QHBoxLayout()
        #horizontalLayout.addWidget(dist_label)
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
            
        self.connect(self.distribution_combo.box, SIGNAL('currentIndexChanged(int)'), self.dist_by_changed)

    def dist_by_changed(self):    
        print 'changing by var'
        widget = self.distribution_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())
            print data
            by_var = unicode(data.toString())
            self.distribution_by_var = by_var                
            self.update_output(self.data)
    
    def set_data(self, output_data):
        self.data = output_data
        self.wght = self.data['wprm']
 
    def set_distribution_by_var_dict(self, description):
        '''
        Use a SystemeSF.description to build the dict ({var: label}) 
        for all the by variable appearing in the distribution view
        '''
        for var in description.col_names:
            var2label = {}
            varcol  = description.get_col(var)
            if isinstance(varcol, EnumCol) or isinstance(varcol, BoolCol) or isinstance(varcol, BoolCol):
                if varcol.label:
                    var2label[varcol.label] = var
                var2label[var] = var
        self.distribution_by_var_dict = var2label
                
    def set_distribution_choices(self, description):
        '''
        Set the variables appearing in the ComboBox 
        '''
        for var in description.col_names:
            var2label = {}
            varcol  = description.get_col(var)
            if isinstance(varcol, EnumCol) or isinstance(varcol, BoolCol) or isinstance(varcol, BoolCol):
                if varcol.label:
                    var2label[varcol.label] = var
                var2label[var] = var
        
        self.set_distribution_by_var_dict(description)
        choices = []
        for var, label in self.distribution_by_var_dict.iteritems():
            choices.append((label,var))
        self.distribution_choices = choices
                
    def update_output(self, output_data):
        print 'update'
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if self.distribution_by_var is not None:
            by_var = self.distribution_by_var
        else:
            by_var = 'typ_men'
        if output_data is None:
            return
        
        self.set_data(output_data)
        self.distribution_combo.box.setEnabled(True)
        print by_var
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


        dist_frame = self.group_by(['revdisp', 'nivvie'], by_var)
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
            

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
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
                         QSpacerItem, QSizePolicy, QApplication, QCursor, QInputDialog, QComboBox)
from PyQt4.QtCore import SIGNAL, Qt, QVariant
from pandas import DataFrame

from core.qthelpers import OfSs
from core.qthelpers import MyComboBox
from core.utils import lorenz, gini

from widgets.matplotlibwidget import MatplotlibWidget
from matplotlib.lines import Line2D
from core.qthelpers import DataFrameViewWidget

class InequalityWidget(QDockWidget):
    def __init__(self, parent = None):
        super(InequalityWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Inequality")
        self.setWindowTitle("Inequality")
        self.dockWidgetContents = QWidget()
        
        widget_list = []


        self.lorenzWidget = MatplotlibWidget(self.dockWidgetContents,
                                              title='Courbe de Lorenz',
                                              xlabel='Population',
                                              ylabel='Variable',
                                              hold=True)
        widget_list.append(self.lorenzWidget)

        
        self.ineqFrameWidget = DataFrameViewWidget(self.dockWidgetContents)
        widget_list.append(self.ineqFrameWidget)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        for widget in widget_list:
            verticalLayout.addWidget(widget)
        self.setWidget(self.dockWidgetContents)

        # Initialize attributes
        self.parent = parent

        self.data = DataFrame() 
        self.data_default = None

        self.vars = {'nivvie' : ['ind', 'men']}
        

    def refresh(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.plot()
        self.update_frame()
        QApplication.restoreOverrideCursor()


    def plot(self):
        '''
        Plots the Lorenz Curve
        '''        
        axes = self.lorenzWidget.axes
        axes.clear()
        output = self.output
        
        idx_weight = {'ind': output._inputs.index['ind'],
                      'men': output._inputs.index['men']}
        weights = {}
        for unit, idx in idx_weight.iteritems():
            weights[unit] = output._inputs.get_value('wprm', idx)
        
        p = []
        l = []
        
        for varname, units in self.vars.iteritems():
            for unit in units:
                
                idx =  output.index[unit]
                values  = output.get_value(varname, idx)
                
                x, y = lorenz(values, weights[unit])         
                gini_coeff = gini(values, weights[unit])
                
                label = varname + ' (' + unit + ') ' + '  Gini:' + str(gini_coeff)
                axes.plot(x,y, linewidth = 2, label = label)
#                p.insert(0, Line2D([0,1],[.5,.5], color =  ))
#                l.insert(0, label)
                
        axes.plot(x,x, label ="")

        axes.legend(loc= 2, prop = {'size':'medium'})
           
            
    def set_data(self, output, default=None):
        '''
        Sets the tables
        '''
        self.output = output
        if default is not None:
            self.data_default = default
        
    def update_frame(self):
        from core.utils import mark_weighted_percentiles
        from pandas import Series

        output = self.output
        for varname, units in self.vars.iteritems():
            for unit in units:
                
                idx =  output.index[unit]
                vals  = output.get_value(varname, idx)
                weights = output._inputs.get_value('wprm', idx)
                champm = output._inputs.get_value('champm', idx)
        
            labels = range(1,11)
            method = 2
            decile, values = mark_weighted_percentiles(vals, labels, weights*champm, method, return_quantiles=True)
            del decile

        
        df = DataFrame( {u'décile' : Series(labels[:-1]), varname : Series(values[1:-1]) })
        print df
        self.ineqFrameWidget.set_dataframe(df)
        self.ineqFrameWidget.reset()
        
    def update_view(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.plot()
        self.update_frame()
        QApplication.restoreOverrideCursor()
        
    def calculated(self):
        self.emit(SIGNAL('calculated()'))
                
    def clear(self):
        pass
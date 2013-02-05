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
from pandas import DataFrame, merge

from src.qt.QtGui import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSortFilterProxyModel,
                         QSpacerItem, QSizePolicy, QPushButton, QInputDialog, QGroupBox)
from src.qt.QtCore import SIGNAL, QSize
from src.qt.compat import from_qvariant

from src.core.qthelpers import OfSs, DataFrameViewWidget, MyComboBox
from src.core.utils.qthelpers import  get_icon
from src.core.simulation import SurveySimulation



from src.plugins.__init__ import OpenfiscaPluginWidget, PluginConfigPage

from src.core.utils_old import of_import
from src.core.baseconfig import get_translation
_ = get_translation('src')


class OpenfiscaPivotTable(object):
    def __init__(self):
        super(OpenfiscaPivotTable, self).__init__()
        
        self.data = DataFrame() # Pandas DataFrame
        self.data_default   = None
        self.by_var_choices = None
        
        # List of variable entering the level 0 (rows) index
        self.row_index = None
        
        # TODO:
        # Dict of variables in the level 1 (columns)
        # exemple { revdisp : { data : [ 'current', 'default'], transform : ['mean', 'median'],  diff: ['absolute', 'relative', 'winners', 'loosers']
    
    
    def set_simulation(self, simulation):
        """
        Set the survey_simulation
        
        Parameters
        ----------
        
        simulation : SurveySimulation
        """
        if isinstance(simulation, SurveySimulation):
            self.simulation = simulation
            self.by_var_choices = self.simulation.var_list
        else:
            raise Exception('OpenfiscaPivotTable:  %s should be an instance of %s class'  %(simulation, SurveySimulation))

    @property
    def vars(self):
        return set(self.simulation.var_list)

    def set_data(self, output_data, default=None):
        self.data = output_data
        if default is not None:
            self.data_default = default
        self.wght = self.data['wprm']

    def get_table(self, by = None, vars = None, entity = None, champm = True, do_not_use_weights = False):
        '''
        Updated frame
        '''
        by_var = by
        if by_var is None:
            raise Exception("OpenfiscaPivotTable : get_table needs a 'by' variable")
        
        if vars is None:
            raise Exception("OpenfiscaPivotTable : get_table needs a 'vars' variable")

        if champm:
            initial_set = set([by_var, 'champm'] + list(vars))
        else:
            initial_set = vars
        
        country = self.simulation.country
        if entity is None:
            ENTITIES_INDEX = of_import(None, 'ENTITIES_INDEX', country) # import ENTITIES_INDEX from country.__init__.py
            entity = ENTITIES_INDEX[0]

        try:
            data, data_default = self.simulation.aggregated_by_entity(entity,  initial_set)
        except:
            self.simulation.compute()
            data, data_default = self.simulation.aggregated_by_entity(entity, initial_set)
            
        self.set_data(data, data_default)        
        
        dist_frame_dict = self.group_by(vars, by_var, champm=champm, do_not_use_weights=do_not_use_weights)
        
        frame = None
        for dist_frame in dist_frame_dict.itervalues():
            if frame is None:
                frame = dist_frame.copy()
            else:
                try:
                    dist_frame.pop('wprm')
                except:
                    pass
                frame = merge(frame, dist_frame, on=by_var)
                
        by_var_label = self.simulation.var2label[by_var]
        if by_var_label == by_var:
            by_var_label = by_var

        enum = self.simulation.var2enum[by_var]                
        frame = frame.reset_index(drop=True)
        
        for col in frame.columns:
            if col[-6:] == "__init":
                frame.rename(columns = { col : self.simulation.var2label[col[:-6]] + " init."}, inplace = True) 
            else:
                frame.rename(columns = { col : self.simulation.var2label[col] }, inplace = True)
        
        if enum is not None:
            frame[by_var_label] = frame[by_var_label].apply(lambda x: enum._vars[x])
               
        return frame
     
    
    def group_by2(self, varlist, category):
        '''
        Computes grouped aggregates
        '''
        datasets = {'data': self.data}
        aggr_dict = {}
    
        if self.data_default is not None:
            datasets['default'] = self.data_default
            
        cols = self.cols
        # cols = []

        for name, data in datasets.iteritems():
            # Computes aggregates by category
            keep = [category, 'wprm', 'champm'] + cols
            temp_data = data[keep].copy()
            temp_data['wprm']   = temp_data['wprm']*temp_data['champm']
            keep.remove('champm')
            del keep['champm']
            temp = []
            for var in varlist:
                temp_data[var] = temp_data['wprm']*data[var]
                temp.append(var)
                keep.append(var)
                    
            from pandas import pivot_table
            aggr_dict[name] = pivot_table(temp_data[keep], cols = cols,
                                  rows = category, values=keep, aggfunc = np.sum)
            
            for cat, df in aggr_dict[name].iterrows():
                for varname in varlist:
                    if name=='default':
                        label = varname + '__init'
                        df[label] = df[varname]/df['wprm']
                        del df[varname]
                    else:
                        df[varname] = df[varname]/df['wprm']
            
            aggr_dict[name].index.names[0] = 'variable'
            aggr_dict[name] = aggr_dict[name].reset_index().unstack(cols.insert(0, 'variable'))

            
        return aggr_dict

    def group_by(self, varlist, category, champm=True, do_not_use_weights=False):
        '''
        Computes grouped aggregates
        '''
        datasets = {'data': self.data}
        aggr_dict = {}
        if self.data_default is not None:
            datasets['default'] = self.data_default

        for name, data in datasets.iteritems():
            # Computes aggregates by category
            keep = [category, 'wprm', 'champm'] 
            temp_data = data[keep].copy()
            temp_data['wprm'] = temp_data['wprm']*temp_data['champm']
            keep.remove('champm')
            del temp_data['champm']
            temp = []
            for var in varlist:
                temp_data[var] = temp_data['wprm']*data[var]
                temp.append(var)
                keep.append(var)
                
            
            grouped = temp_data[keep].groupby(category, as_index = False)
            aggr_dict[name] = grouped.aggregate(np.sum)

            # Normalizing to have the average
            for varname in temp:
                if name=='default':
                    label = varname + '__init'
                    aggr_dict[name][label] = aggr_dict[name][varname]/aggr_dict[name]['wprm']
                    del aggr_dict[name][varname]
                else:
                    aggr_dict[name][varname] = aggr_dict[name][varname]/aggr_dict[name]['wprm']
                              
        return aggr_dict


    def clear(self):
        self.view.clear()
        self.data = None
        self.wght = None

class DistributionConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Distribution")
        
    def setup_page(self):
        variables_group = QGroupBox(_("Distribution"))

        # Index variable (byvar)
        names = ['so']
        choices = zip(names, names)
        byvar_combo = self.create_combobox(_("Index variables: "),
                                        choices, 'byvar')

        # Column variables
        names = ['nivvie']
        choices = zip(names, names)
        colvar_combo = self.create_combobox(_("Column variables: "),
                                        choices, 'colvar')

        variables_layout = QVBoxLayout()
        variables_layout.addWidget(byvar_combo)
        variables_layout.addWidget(colvar_combo)
        variables_group.setLayout(variables_layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(variables_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


    
class DistributionWidget(OpenfiscaPluginWidget):
    """
    Distribution Widget
    """
    CONF_SECTION = 'distribution'
    CONFIGWIDGET_CLASS = DistributionConfigPage
    
    def __init__(self, parent = None):
        super(DistributionWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Distribution")
        self.setWindowTitle("Distribution")
        self.dockWidgetContents = QWidget()
        
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

        add_var_btn  = self.add_toolbar_btn(tooltip = u"Ajouter une variable de calage",
                                        icon = "list-add.png")
        
        rmv_var_btn = self.add_toolbar_btn(tooltip = u"Retirer une variable de calage",
                                        icon = "list-remove.png")

        toolbar_btns = [add_var_btn, rmv_var_btn] #rst_var_btn
        

        distribLayout = QHBoxLayout()
        for btn in toolbar_btns:
            distribLayout.addWidget(btn)
        distribLayout.addWidget(self.distribution_combo)
        distribLayout.addItem(spacerItem)
        
        self.view = DataFrameViewWidget(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addLayout(distribLayout)
        verticalLayout.addWidget(self.view)
                
        self.connect(add_var_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(rmv_var_btn, SIGNAL('clicked()'), self.remove_var)

        # Initialize attributes
        self.parent = parent
        self.openfisca_pivot_table = None
        self.distribution_by_var = None
        self.selected_vars = None
        
        self.setLayout(verticalLayout)
        self.initialize()

    def add_toolbar_btn(self, tooltip = None, icon = None):
        btn = QPushButton(self)
        if tooltip:
            btn.setToolTip(tooltip)
        if icon:
            icn = get_icon(icon)
            btn.setIcon(icn)
            btn.setIconSize(QSize(22, 22))
        return btn

    def initialize(self):
        
        self.distribution_by_var = 'so'
        self.selected_vars = set(['revdisp', 'nivvie']) 
        

    def set_openfisca_pivot_table(self, openfisca_pivot_table):
        self.openfisca_pivot_table = openfisca_pivot_table
        self.vars = self.openfisca_pivot_table.vars 
        self.set_distribution_choices()
    
    def add_var(self):
        var = self.ask()
        if var is not None:
            self.selected_vars.add(var)
            self.refresh_plugin()
        else:
            return
    
    def remove_var(self):
        var = self.ask(remove=True)
        if var is not None:
            self.selected_vars.remove(var)
            self.refresh_plugin()
        else:
            return

    def ask(self, remove=False):
        self.vars = self.openfisca_pivot_table.vars
        if not remove:
            dialog_label = "Ajouter une variable"
            choices = self.vars - self.selected_vars
        else:
            choices =  self.selected_vars
            dialog_label = "Retirer une variable"
            
        dialog_choices = sorted([self.openfisca_pivot_table.simulation.var2label[variab] for variab in list(choices)])
        label, ok = QInputDialog.getItem(self, dialog_label , "Choisir la variable", 
                                       dialog_choices)
        if ok and label in dialog_choices:
            return self.openfisca_pivot_table.simulation.label2var[unicode(label)] 
        else:
            return None 

    def dist_by_changed(self):    
        widget = self.distribution_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())
            by_var = unicode( from_qvariant(data))

            self.distribution_by_var = by_var                
            self.refresh_plugin()
                     
    def set_distribution_choices(self):
        '''
        Set the variables appearing in the ComboBox 
        '''
        combobox = self.distribution_combo.box
        combobox.setEnabled(True)
        self.disconnect(combobox, SIGNAL('currentIndexChanged(int)'), self.dist_by_changed)
        self.distribution_combo.box.clear()
        
        if self.openfisca_pivot_table is not None:
            choices = set( self.openfisca_pivot_table.by_var_choices )
            var2label = self.openfisca_pivot_table.simulation.var2label
        else:
            choices = []
        
        for var in choices:
            combobox.addItem(var2label[var], var )

        if hasattr(self, 'distribution_by_var'):
            index = combobox.findData(self.distribution_by_var)
            if index != -1:
                combobox.setCurrentIndex(index)
        
        self.connect(self.distribution_combo.box, SIGNAL('currentIndexChanged(int)'), self.dist_by_changed)
        self.distribution_combo.box.model().sort(0)



    def calculated(self):
        '''
        Emits signal indicating that aggregates are computed
        '''
        self.emit(SIGNAL('calculated()'))


    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return "Distribution"

    
    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see SpyderPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')
    
    def refresh_plugin(self):
        '''
        Update distribution view
        '''
        self.starting_long_process(_("Refreshing distribution table ..."))

        by_var = self.distribution_by_var
        selection = self.selected_vars
        if self.openfisca_pivot_table is not None:
            frame = self.openfisca_pivot_table.get_table(by = by_var, vars = selection)
            self.view.set_dataframe(frame)
        self.view.reset()
        self.calculated()
        self.ending_long_process(_("Distribution table refreshed"))

    def get_plugin_actions(self):
        """
        Return a list of actions related to plugin
        Note: these actions will be enabled when plugin's dockwidget is visible
              and they will be disabled when it's hidden
        """
        raise NotImplementedError
    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.main.add_dockwidget(self)
        dist = OpenfiscaPivotTable()
        dist.set_simulation(self.main.survey_simulation)
        self.set_openfisca_pivot_table(dist)
        

    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        
        return True
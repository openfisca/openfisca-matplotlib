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

from os import path
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
                         QSpacerItem, QSizePolicy, QApplication, QCursor, QInputDialog)
from PyQt4.QtCore import SIGNAL, Qt, QVariant

from pandas import DataFrame
from src.core.qthelpers import OfSs, DataFrameViewWidget
from src.core.qthelpers import MyComboBox
from src.core.columns import EnumCol


from src.qt.QtGui import QGroupBox, QVBoxLayout
from src.core.config import CONF, get_icon
from src.plugins.__init__ import OpenfiscaPluginWidget, PluginConfigPage

from src.core.utils_old import of_import
from src.core.baseconfig import get_translation

_ = get_translation('survey_explorer', 'src.plugins.survey')


class SurveyExplorerConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Survey data explorer")
        
    def setup_page(self):

        # TODO: redo completely
        legend_group = QGroupBox(_("Export"))
        choices = [('cvs', 'csv'),
                   ('xls', 'xls'),]
        table_format = self.create_combobox(_('Table export format'), choices, 'format')
        
        #xaxis  
        
        layout = QVBoxLayout()
        layout.addWidget(table_format)
        legend_group.setLayout(layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(legend_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class SurveyExplorerWidget(OpenfiscaPluginWidget):    
    """
    Survey data explorer Widget
    """
    CONF_SECTION = 'survey'
    CONFIGWIDGET_CLASS = SurveyExplorerConfigPage

    def __init__(self, parent = None):
        super(SurveyExplorerWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("ExploreData")
        self.setWindowTitle("ExploreData")
        self.dockWidgetContents = QWidget()
        
        self.data_label = QLabel("Data", self.dockWidgetContents)

        self.add_btn = QPushButton(u"Ajouter variable",self.dockWidgetContents)        
        self.remove_btn = QPushButton(u"Retirer variable",self.dockWidgetContents)  
        self.datatables_choices = []
        self.datatable_combo = MyComboBox(self.dockWidgetContents, u'Choix de la table', self.datatables_choices) 
        
#        self.add_btn.setDisabled(True)
#        self.remove_btn.setDisabled(True)
        
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.add_btn)
        horizontalLayout.addWidget(self.remove_btn)
        horizontalLayout.addWidget(self.datatable_combo)
        horizontalLayout.addItem(spacerItem)
        self.view = DataFrameViewWidget(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.data_label)

        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(self.view)
        self.setLayout(verticalLayout)

        # Initialize attributes
        self.parent = parent

        self.selected_vars = set()
        self.data = DataFrame() 
        self.view_data = None
        self.dataframes = {}
        self.vars = set()

        self.connect(self.add_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(self.remove_btn, SIGNAL('clicked()'), self.remove_var)
        self.connect(self.datatable_combo.box, SIGNAL('currentIndexChanged(int)'), self.select_data)        

        self.update_btns()


    def set_simulation(self, survey_simulation):
        """
        Set survey_simulation
        """
        
        country = CONF.get('parameters', 'country')
        datesim = CONF.get('parameters', 'datesim')
        reforme = CONF.get('survey', 'reforme')
        year = datesim.year
        survey_simulation.set_config(year = year, country = country, reforme = reforme)
        self.survey_simulation = survey_simulation

        
    def load_from_file(self):        
        fname = CONF.get('survey', 'data_file')
        if path.isfile(fname):
            self.survey_simulation.set_survey(filename = fname)
            return True
                
                
    def set_year(self, year):
        '''
        Sets year in label
        '''
        self.data_label.setText("Survey data from year " + str(year))

    def update_btns(self):
        if (self.vars - self.selected_vars):
            self.add_btn.setEnabled(True)
        if self.selected_vars:
            self.remove_btn.setEnabled(True)
            
    def update_choices(self):
        box = self.datatable_combo.box
        box.clear()
        for name, key in self.datatables_choices:
            box.addItem(name, QVariant(key))

    def select_data(self):
        widget = self.datatable_combo.box
        dataframe_name = unicode(widget.itemData(widget.currentIndex()).toString())
        if dataframe_name: # to deal with the box.clear() 
            self.set_dataframe(name = dataframe_name)
        self.update_btns()

    def add_dataframe(self, dataframe, name = None):
        '''
        Adds a dataframe to the list o the available dataframe 
        '''
        if name == None:
            name = "dataframe" + len(self.dataframes.keys())
    
#        if not self.data:
#            self.dataframes = {}

        self.dataframes[name] = dataframe
        self.datatables_choices.append((name, name))
        self.update_choices()
        self.update_btns()

    def set_dataframe(self, dataframe = None, name = None):
        '''
        Sets the current dataframe
        '''
        if name is not None:
            self.data = self.dataframes[name]
        if dataframe is not None:
            self.data = dataframe
            
        self.vars = set(self.data.columns)
        self.update_btns()

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

    def add_var(self):
        var = self.ask()
        if var is not None:
            self.selected_vars.add(var)
            self.update_view()
        else:
            return
    
    def remove_var(self):
        var = self.ask(remove=True)
        if var is not None:
            self.selected_vars.remove(var)
            self.update_view()
        else:
            return
                         
    def set_choices(self, description):
        '''
        Set the variables appearing in the add and remove dialogs 
        '''     
        data_vars = set(self.data.columns)
        label2var = {}
        var2label = {}
        var2enum = {}
        for var in description.col_names:
            varcol  = description.get_col(var)
            if isinstance(varcol, EnumCol): 
                var2enum[var] = varcol.enum
                if varcol.label:
                    label2var[varcol.label] = var
                    var2label[var]          = varcol.label
                else:
                    label2var[var] = var
                    var2label[var] = var
        
        all_labels = set(label2var.values()).intersection(data_vars)
        
        self.var2label = var2label
        self.var2enum  = var2enum
        
    def update_view(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not self.selected_vars:
            self.view.clear()
            QApplication.restoreOverrideCursor()
            return
        
        cols = self.selected_vars
        if self.view_data is None:
            self.view_data = self.data[list(cols)]
        
        new_col = cols - set(self.view_data)
        if new_col:
            self.view_data[list(new_col)] = self.data[list(new_col)] 
            df = self.view_data
        else:
            df = self.view_data[list(cols)]
    
        self.view.set_dataframe(df)

        self.view.reset()
        self.update_btns()
        QApplication.restoreOverrideCursor()
        
    def calculated(self):
        self.emit(SIGNAL('calculated()'))
                
    def clear(self):
        self.view.clear()
        self.data = None
        self.datatables_choices = []
        self.dataframes = {}
        self.update_btns()
        
        
    #------ OpenfiscaPluginMixin API ---------------------------------------------
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return "Survey Explorer"

    
    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see SpyderPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')
            
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


    def refresh_plugin(self):
        '''
        Update Scenario Table
        '''
        pass
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True

        
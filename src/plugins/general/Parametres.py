# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

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


from src.gui.qt.QtGui import QFileDialog, QMessageBox
from src.gui.qt.QtCore import SIGNAL, QDate

from src.gui.views.ui_parametres import Ui_Parametres
from src.parametres.paramData import XmlReader, Tree2Object
from src.parametres.paramModel import PrestationModel
from src.parametres.Delegate import CustomDelegate, ValueColumnDelegate

from src.gui.baseconfig import get_translation
from src.gui.utils.qthelpers import get_icon
import os
_ = get_translation('src')

from src.gui.qt.QtGui import QGroupBox, QVBoxLayout
from src.plugins.__init__ import OpenfiscaPluginWidget, PluginConfigPage


class ParametersConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Legislatives parameters")

    def setup_page(self):

        group = QGroupBox(_("Legislation"))

        # Country
        names = ['france', 'tunisia']
        choices = zip(names, names)
        country_combo = self.create_combobox(_("Country: "), # TODO: _
                                        choices, 'country')

        # Date
        from src.gui.config import CONF
        default = CONF.get('parameters', 'datesim')
        date_dateedit = self.create_dateedit(prefix=_("Legislation date"),
                                             option= 'datesim', 
                                             default = default,
                                             min_ = "2002-01-01", 
                                             max_ = "2012-12-31")
        
        layout = QVBoxLayout()
        layout.addWidget(country_combo)
        layout.addWidget(date_dateedit)
        group.setLayout(layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class ParamWidget(OpenfiscaPluginWidget, Ui_Parametres):
    """
    Parameters Widget
    """
    CONF_SECTION = 'parameters'
    CONFIGWIDGET_CLASS = ParametersConfigPage

    def __init__(self, parent = None):
        super(ParamWidget, self).__init__(parent)
        self.setupUi(self)
        self.setLayout(self.verticalLayout)
        
        self.__parent = parent

        self.connect(self.save_btn, SIGNAL("clicked()"), self.saveXml)
        self.connect(self.open_btn, SIGNAL("clicked()"), self.loadXml)
        self.connect(self.reset_btn, SIGNAL("clicked()"), self.reset)
        
        self.initialize()


    #------ Public API ---------------------------------------------

    def reset(self):
        self.initialize()
        self.changed()
            
    def changed(self):
        self.emit(SIGNAL('changed()'))
    
    def initialize(self):
        country = self.get_option('country')
        self._file = 'countries/' + country + '/param/param.xml'
        
        value = self.get_option('datesim')
        from datetime import datetime
        self._date = datetime.strptime(value ,"%Y-%m-%d").date()

        
        self.label.setText(u"Date : %s" %( str(self._date)) )
        self._reader = XmlReader(self._file, self._date)
        self._rootNode = self._reader.tree
        self._rootNode.rmv_empty_code()
                
        self._model = PrestationModel(self._rootNode, self)
        self.connect(self._model, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.changed)

        self.uiTree.setModel(self._model)
        self.selectionModel = self.uiTree.selectionModel()
        self.uiTree.setColumnWidth(0,230)
        self.uiTree.setColumnWidth(1,70)
        self.uiTree.setColumnWidth(2,70)
        delegate = CustomDelegate(self)
        delegate.insertColumnDelegate(1, ValueColumnDelegate(self))
        delegate.insertColumnDelegate(2, ValueColumnDelegate(self))
        self.uiTree.setItemDelegate(delegate)
    
    def getParam(self, defaut = False):
        obj = Tree2Object(self._rootNode, defaut)
        obj.datesim = self._date
        return obj

    def saveXml(self):
        reformes_dir = self.get_option('reformes_dir')
        default_fileName = os.path.join(reformes_dir, 'sans-titre')
        fileName = QFileDialog.getSaveFileName(self,
                                               _("Save a reform"), default_fileName, u"Paramètres OpenFisca (*.ofp)")
        if fileName:
#            try:
                self._rootNode.asXml(fileName)
#            except Exception, e:
#                QMessageBox.critical(
#                    self, "Erreur", u"Impossible d'enregistrer le fichier : " + str(e),
#                    QMessageBox.Ok, QMessageBox.NoButton)


    def loadXml(self):
        reformes_dir = self.get_option('reformes_dir')
        fileName = QFileDialog.getOpenFileName(self,
                                               _("Open a reform"), reformes_dir, u"Paramètres OpenFisca (*.ofp)")
        if not fileName == '':
            try: 
                loader = XmlReader(str(fileName))
                self.set_option('datesim',str(loader._date))
                self.initialize()
                self._rootNode.load(loader.tree)
                self.changed()
            except Exception, e:
                QMessageBox.critical(
                    self, _("Error"), _("Unable to read the following file : ") + str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)

    #------ OpenfiscaPluginMixin API ---------------------------------------------

    def apply_plugin_settings(self, options):
        """
        Apply configuration file's plugin settings
        """
        if 'country' in options:
            country = self.get_option('country')
            NotImplementedError
#            self.main.close()
#            from src.of_test import main
#            main()
            
        if 'datesim' in options:
            
            datesim = self.get_option('datesim')
            self.main.scenario_simulation.set_config(year = datesim[0:4])
            if self.main.survey_explorer.get_option('enable'):
                self.main.register_survey_widgets(True)
            
            self.reset()
    
    
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return "Parameters"

    
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
        return []
    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.main.add_dockwidget(self)
        self.connect(self, SIGNAL('changed()'), self.main.parameters_changed)

    def refresh_plugin(self):
        '''
        Update
        '''
        pass
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True
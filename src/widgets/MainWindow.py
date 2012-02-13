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

import platform
from PyQt4.QtCore import (SIGNAL, SLOT, Qt, QSettings, QVariant, QSize, QPoint, 
                          PYQT_VERSION_STR, QT_VERSION_STR)
from PyQt4.QtGui import (QMainWindow, QMessageBox, QKeySequence, QAction, QIcon, 
                         QApplication, QCursor, QPixmap, QSplashScreen, QColor,
                         QActionGroup)

from datetime import datetime
from Config import CONF, VERSION, SimConfigPage, ConfigDialog
from views import ui_mainwindow
from widgets.Parametres import ParamWidget
from widgets.Composition import ScenarioWidget
from widgets.Output import Graph, OutTable
from Utils import Scenario
from france.data import InputTable
from france.model import Model
from core.utils import gen_output_data
# import resources_rc

class MainWindow(QMainWindow, ui_mainwindow.Ui_MainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.dirty = False
        self.isLoaded = False
        
        # Showing splash screen
        pixmap = QPixmap(':/images/splash.png', 'png')
        self.splash = QSplashScreen(pixmap)
        font = self.splash.font()
        font.setPixelSize(10)
        self.splash.setFont(font)
        self.splash.show()
        self.splash.showMessage("Initialisation...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
#        if CONF.get('main', 'current_version', '') != __version__:
#            CONF.set('main', 'current_version', __version__)
            # Execute here the actions to be performed only once after
            # each update (there is nothing there for now, but it could 
            # be useful some day...
        
        self.scenario = Scenario()
        # Preferences
        self.general_prefs = [SimConfigPage]
        self.oldXAXIS = 'sal'
        self.reforme = False
        self.apply_settings()
        
        # Creation des dockwidgets
        self.create_dockwidgets()
        self.populate_mainwidow()
        self.centralwidget.hide()

        # Initialisation des menus
        # Menu Fichier
        self.connect(self.actFileQuit, SIGNAL('triggered()'), SLOT('close()'))
        self.connect(self.actFileRefresh, SIGNAL('triggered()'), self.refresh)
        self.connect(self.actModeReforme, SIGNAL('triggered(bool)'), self.modeReforme)
        self.connect(self.actPreferences, SIGNAL('triggered()'), self.edit_preferences)
        self.connect(self.actExportCsv, SIGNAL('triggered()'), self._table.saveCsv)
        self.connect(self.actExportPng, SIGNAL('triggered()'), self._graph.save_figure)

        # Menu Mode
        modeGroup = QActionGroup(self)
        modeGroup.addAction(self.actBareme)
        modeGroup.addAction(self.actCasType)
        self.mode = 'bareme'
        self.actBareme.trigger()
        self.connect(self.actBareme,  SIGNAL('triggered()'), self.modeBareme)
        self.connect(self.actCasType, SIGNAL('triggered()'), self.modeCasType)
        
        self.connect(self._menage,     SIGNAL('changed()'), self.changed)
        self.connect(self._parametres, SIGNAL('changed()'), self.changed)
        
        # Menu Help
        helpAboutAction = self.createAction(u"&About OpenFisca", self.helpAbout)
        helpHelpAction = self.createAction("&Aide", self.helpHelp, QKeySequence.HelpContents)
        help_menu = self.menuBar().addMenu("&Aide")
        self.addActions(help_menu, (helpAboutAction, helpHelpAction))
                
        # Menu Affichage
        view_menu = self.createPopupMenu()
        view_menu.setTitle("&Affichage")
        self.menuBar().insertMenu(help_menu.menuAction(),
                                  view_menu)
        
        # Window settings
        settings = QSettings()
        size = settings.value('MainWindow/Size', QVariant(QSize(800,600))).toSize()
        self.resize(size)
        position = settings.value('MainWindow/Position', QVariant(QPoint(0,0))).toPoint()
        self.move(position)
        self.restoreState(settings.value("MainWindow/State").toByteArray())

        self.refresh()
        self.isLoaded = True
        self.splash.hide()

    
    def create_dockwidgets(self):
        # Création des dockwidgets
        self._parametres = ParamWidget('data/param.xml', self)
        self._menage = ScenarioWidget(self.scenario, self)
        self._graph = Graph(self)
        self._table = OutTable(self)
        
    def populate_mainwidow(self):
        self.addDockWidget(Qt.RightDockWidgetArea, self._parametres)
        self.addDockWidget(Qt.RightDockWidgetArea, self._menage)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._graph)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._table)
        self.tabifyDockWidget(self._table, self._graph)

    def modeReforme(self, b):
        self.reforme = b
        self.changed()

    def modeBareme(self):
        self.mode = 'bareme'
        NMEN = CONF.get('simulation', 'nmen')
        if NMEN == 1: CONF.set('simulation', 'nmen', 101)
        self.changed()

    def modeCasType(self):
        self.mode = 'castype'
        CONF.set('simulation', 'nmen', 1)
        self.changed()

    def refresh(self):
        # On vérifie que le ménage est valide
        msg = self.scenario.check_consistency()
        if msg:
            QMessageBox.critical(self, u"Ménage non valide",
                                 msg, 
                                 QMessageBox.Ok, QMessageBox.NoButton)
            return False
        # Si oui, on lance le calcul
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.statusbar.showMessage(u"Calcul en cours...")
        self.actFileRefresh.setEnabled(False)
        # set the table model to None before changing data
        self._table.clearModel()
        
        P_default = self._parametres.getParam(defaut = True)    
        P_courant = self._parametres.getParam(defaut = False)
        
        input_table = InputTable()
        input_table.populate_from_scenario(self.scenario)
        population_courant = Model(P_courant, P_default)
        population_courant.set_inputs(input_table)
        data_courant = gen_output_data(population_courant)

        if self.reforme:
            population_courant.reset()
            population_default = Model(P_default, P_default)
            population_default.set_inputs(input_table)
            data_default = gen_output_data(population_default)
            data_courant.difference(data_default)
        else:
            data_default = data_courant
        self._table.updateTable(data_courant, reforme = self.reforme, mode = self.mode, dataDefault = data_default)
        self._graph.updateGraph(data_courant, reforme = self.reforme, mode = self.mode, dataDefault = data_default)

        self.statusbar.showMessage(u"")
        QApplication.restoreOverrideCursor()
        
    def closeEvent(self, event):
        if self.okToContinue():
            settings = QSettings()
            settings.setValue('MainWindow/Size', QVariant(self.size()))
            settings.setValue('MainWindow/Position', QVariant(self.pos()))
            settings.setValue('MainWindow/State', QVariant(self.saveState()))
        else:
            event.ignore()
    
    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self, 
                                         "OpenFisca",
                                         "Voulez-vous quitter ?",
                                         QMessageBox.Yes|QMessageBox.No)
            if reply == QMessageBox.No:
                return False
        return True
    
    def helpAbout(self):
        QMessageBox.about(self, u"About OpenFisca",
                          u''' <b>OpenFisca</b><sup>beta</sup> v %s
                          <p> Copyright &copy; 2011 Clément Schaff, Mahdi Ben Jelloul
                          Tout droit réservé
                          <p> License GPL version 3 ou supérieure
                          <p> Python %s - Qt %s - PyQt %s on %s'''
                          % (VERSION, platform.python_version(),
                          QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))

    def helpHelp(self):
        QMessageBox.about(self, u"Aide OpenFisca",
                          u'''<p> L'aide n'est pas disponible pour le moment. Pour plus
                          d'information, aller à <a href = www.openfisca.fr> www.openfisca.fr </a>
                          ''')

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
    
    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def apply_settings(self):
        """Apply settings changed in 'Preferences' dialog box"""
        self.XAXIS = CONF.get('simulation', 'xaxis')
        if not self.XAXIS == self.oldXAXIS:
            self.scenario.indiv[0][self.oldXAXIS + 'i']=0
        if self.isLoaded == True:
            self._parametres.initialize()
            self.refresh()

    def edit_preferences(self):
        """Edit OpenFisca preferences"""
        dlg = ConfigDialog(self)
        for PrefPageClass in self.general_prefs:
            widget = PrefPageClass(parent = dlg, main=self)
            widget.initialize()
            dlg.add_page(widget)

        dlg.show()
        dlg.check_all_settings()
        dlg.exec_()

    def changed(self):
        self.statusbar.showMessage(u"Appuyez sur F9 pour lancer la simulation")
        self.actFileRefresh.setEnabled(True)

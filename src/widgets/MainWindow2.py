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

from os import path
from PyQt4.QtCore import (SIGNAL, SLOT, Qt, QSettings, QVariant, QSize, QPoint, 
                          PYQT_VERSION_STR, QT_VERSION_STR, QLocale)
from PyQt4.QtGui import (QMainWindow, QWidget, QGridLayout, QMessageBox, QKeySequence,
                         QApplication, QCursor, QPixmap, QSplashScreen, QColor,
                         QActionGroup, QStatusBar)

from Config import CONF, VERSION, ConfigDialog, SimConfigPage, PathConfigPage, CalConfigPage
from widgets.Parametres import ParamWidget
from src.plugins.scenario.table import OutTable
from src.plugins.scenario.graph import Graph
from src.plugins.survey.aggregates import Aggregates, AggregateOutputWidget
from src.plugins.survey.distribution import OFPivotTable, DistributionWidget
from widgets.Calibration import CalibrationWidget
from widgets.Inflation import InflationWidget
from widgets.ExploreData import ExploreDataWidget
from widgets.Inequality import InequalityWidget
from core.utils import of_import
from core.qthelpers import create_action, add_actions, get_icon
from core.simulation import SurveySimulation, ScenarioSimulation
import gc


class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.dirty = False
        self.isLoaded = False
        self.calibration_enabled = False
        self.inflation_enabled = False
        self.aggregate_enabled = False

        self.setObjectName("MainWindow")
        self.resize(800, 600)
        self.setWindowTitle("OpenFisca")
        app_icon = get_icon('OpenFisca22.png')
        self.setWindowIcon(app_icon)
        self.setLocale(QLocale(QLocale.French, QLocale.France))
        self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)

        self.centralwidget = QWidget(self)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.hide()

        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

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
        
        self.start()
        
    def start(self, restart = False):

        self.survey_simulation = SurveySimulation()
        self.scenario_simulation = ScenarioSimulation()

        # Preferences
        self.general_prefs = [SimConfigPage, PathConfigPage, CalConfigPage]
        self.reforme = False
        
        self.apply_settings()
        
        # Dockwidgets creation
        self.splash.showMessage("Creating widgets...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))

        self.create_dockwidgets()
        self.populate_mainwidow()

        #################################################################
        ## Menu initialization
        #################################################################
        self.splash.showMessage("Creating menubar...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        # Menu Fichier
        self.file_menu = self.menuBar().addMenu("Fichier")
        action_export_png = create_action(self, 'Exporter le graphique', icon = 'document-save png.png', triggered = self._graph.save_figure)
        action_export_csv = create_action(self, 'Exporter la table (cas type)', icon = 'document-save csv.png', triggered = self._table.save_table)
        action_export_agg = create_action(self, u"Exporter la table (aggrégats)", icon = 'document-save csv.png', triggered = self._aggregate_output_widget.save_table)        
        action_pref = create_action(self, u'Préférences', QKeySequence.Preferences, icon = 'preferences-desktop.png', triggered = self.edit_preferences)
        action_quit = create_action(self, 'Quitter', QKeySequence.Quit, icon = 'process-stop.png',  triggered = SLOT('close()'))
        
        file_actions = [action_export_png, action_export_csv,None, action_pref, None, action_quit]
        add_actions(self.file_menu, file_actions)

        # Menu Edit
        self.edit_menu = self.menuBar().addMenu(u"Édition")
        action_copy = create_action(self, 'Copier', QKeySequence.Copy, triggered = self.global_callback, data = 'copy')
        
        edit_actions = [None, action_copy]
        add_actions(self.edit_menu, edit_actions)

        # Menu Simulation
        self.simulation_menu = self.menuBar().addMenu(u"Simulation")

        self.action_refresh_bareme      = create_action(self, u'Calculer barèmes', shortcut = 'F9', icon = 'calculator_green.png', triggered = self.refresh_bareme)
        self.action_refresh_aggregate   = create_action(self, u'Calculer aggrégats', shortcut = 'F10', icon = 'calculator_blue.png', triggered = self.refresh_aggregate)

        self.action_calibrate = create_action(self, u'Caler les poids', shortcut = 'CTRL+K', icon = 'scale22.png', triggered = self.calibrate)
        self.action_inflate = create_action(self, u'Inflater les montants', shortcut = 'CTRL+I', icon = 'scale22.png', triggered = self.inflate)

        action_bareme = create_action(self, u'Barème', icon = 'bareme22.png', toggled = self.modeBareme)
        action_cas_type = create_action(self, u'Cas type', icon = 'castype22.png', toggled = self.modeCasType)
        action_mode_reforme = create_action(self, u'Réforme', icon = 'comparison22.png', toggled = self.modeReforme, tip = u"Différence entre la situation simulée et la situation actuelle")
        mode_group = QActionGroup(self)
        mode_group.addAction(action_bareme)
        mode_group.addAction(action_cas_type)
        self.mode = 'bareme'
        action_bareme.trigger()

        simulation_actions = [self.action_refresh_bareme, self.action_refresh_aggregate , None, self.action_calibrate, self.action_inflate, None, action_bareme, action_cas_type, None, action_mode_reforme]
        add_actions(self.simulation_menu, simulation_actions)
        
        # Menu Help
        help_menu = self.menuBar().addMenu("&Aide")
        action_about = create_action(self, u"&About OpenFisca", triggered = self.helpAbout)
        action_help = create_action(self, "&Aide", QKeySequence.HelpContents, triggered = self.helpHelp)
        help_actions = [action_about, action_help]
        add_actions(help_menu, help_actions)
                
        # Display Menu
        view_menu = self.createPopupMenu()
        view_menu.setTitle("&Affichage")
        self.menuBar().insertMenu(help_menu.menuAction(),
                                  view_menu)
        
        # Toolbar
        self.main_toolbar = self.create_toolbar(u"Barre d'outil", 'main_toolbar')
        toolbar_actions = [self.action_refresh_bareme, action_export_png, action_export_csv, None, 
                           self.action_refresh_aggregate, action_export_agg, None, self.action_calibrate, None, self.action_inflate, None,
                            action_bareme, action_cas_type, None, action_mode_reforme]
        add_actions(self.main_toolbar, toolbar_actions)


        self.connect(self._menage,     SIGNAL('changed()'), self.changed_bareme)
        self.connect(self._parametres, SIGNAL('changed()'), self.changed_param)
        self.connect(self._aggregate_output_widget, SIGNAL('calculated()'), self.calculated)
        self.connect(self, SIGNAL('weights_changed()'), self.refresh_aggregate)
        self.connect(self, SIGNAL('inflated()'), self.refresh_aggregate)
        self.connect(self, SIGNAL('bareme_only()'), self.switch_bareme_only)
        
        # Window settings
        self.splash.showMessage("Restoring settings...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        settings = QSettings()
        size = settings.value('MainWindow/Size', QVariant(QSize(800,600))).toSize()
        self.resize(size)
        position = settings.value('MainWindow/Position', QVariant(QPoint(0,0))).toPoint()
        self.move(position)
        self.restoreState(settings.value("MainWindow/State").toByteArray())

        self.splash.showMessage("Loading survey data...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        
        self.enable_aggregate(True)

        self.splash.showMessage("Refreshing bareme...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))        
        
        self.refresh_bareme()
        
        if self.aggregate_enabled:
            self.splash.showMessage("Refreshing aggregate...", Qt.AlignBottom | Qt.AlignCenter | 
                                    Qt.AlignAbsolute, QColor(Qt.black))        

            self.refresh_aggregate()
        
        self.isLoaded = True
        self.splash.hide()

    def create_toolbar(self, title, object_name, iconsize=24):
        toolbar = self.addToolBar(title)
        toolbar.setObjectName(object_name)
        toolbar.setIconSize( QSize(iconsize, iconsize) )
        return toolbar

    def create_dockwidgets(self):
        # Création des dockwidgets
        self._parametres = ParamWidget(self)
        ScenarioWidget = of_import('widgets.Composition', 'ScenarioWidget')
        self._menage = ScenarioWidget(scenario = self.scenario_simulation.scenario, parent = self)
        self._graph = Graph(self)
        self._table = OutTable(self)
        
        widget_classes = [AggregateOutputWidget, DistributionWidget, ExploreDataWidget, InequalityWidget]
        agg_widget_classes = [AggregateOutputWidget, DistributionWidget, InequalityWidget, ExploreDataWidget]

        from core.utils import lower_and_underscore
        self.aggregate_widgets = []                
        for widget_class in widget_classes:
            widget_name = lower_and_underscore(widget_class.__name__)
            setattr(self, widget_name, widget_class(self))
            if widget_class in agg_widget_classes:
                self.aggregate_widgets.append( getattr(self, widget_name))

        
    def populate_mainwidow(self):
        '''
        Creates all dockwidgets
        '''
        self.addDockWidget(Qt.RightDockWidgetArea, self._parametres)
        self.addDockWidget(Qt.RightDockWidgetArea, self._menage)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._graph)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._table)
        
        self.tabifyDockWidget(self._table, self._graph)
        
        for widget in self.aggregate_widgets:
            self.addDockWidget(Qt.LeftDockWidgetArea, widget)
            self.tabifyDockWidget(self._table, widget)
        
        
    def global_callback(self):
        """Global callback"""
        widget = QApplication.focusWidget()
        action = self.sender()
        callback = unicode(action.data().toString())
        if hasattr(widget, callback):
            getattr(widget, callback)()

    def load_survey_data(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            # liberate some memory before loading new data
            self.reset_aggregate()
            fname = CONF.get('paths', 'survey_data/file')
            if path.isfile(fname):
                self.survey_simulation.set_survey(filename = fname)
                return True
        except Exception, e:
            self.aggregate_enabled = False
            QMessageBox.warning(self, u"Impossible de lire les données", 
                                u"OpenFisca n'a pas réussi à lire les données d'enquête et passe en mode barème. " + 
                                u"L'erreur suivante a été renvoyée:\n%s\n\nVous pouvez charger des nouvelles données d'enquête dans Fichier>Paramètres>Chemins>Données d'enquête"%e)
            self.emit(SIGNAL('baremeOnly()'))
            return False
        finally:
            QApplication.restoreOverrideCursor()
        
    def enable_aggregate(self, val = True):
        '''
        Enables computation of aggregates
        '''
        survey_enabled = CONF.get('paths', 'survey_data/survey_enabled')
        
        loaded = False
        reloaded = False        
        if val and survey_enabled:        
            if self.aggregate_enabled:
                year = CONF.get('simulation','datesim').year    
                if self.survey_simulation.survey.survey_year != year:
                    loaded = self.load_survey_data()
                    reloaded = True
                else:
                    loaded = True
            else:
                loaded = self.load_survey_data()

        if loaded:
            # Show widgets and enabled actions
            self.aggregate_enabled = True
            self._aggregate_output_widget.setEnabled(True)

            if not reloaded:            
                for widget in self.aggregate_widgets:
                    widget.show()
            
            self.action_refresh_aggregate.setEnabled(True)
            if reloaded:
                print "reloading"
                self.refresh_aggregate()
            
            self.action_calibrate.setEnabled(True)
            self.action_inflate.setEnabled(True)
        else:
            self.switch_bareme_only()

    def switch_bareme_only(self):
            self.aggregate_enabled = False
            self._aggregate_output_widget.setEnabled(False)
            for widget in self.aggregate_widgets:
                widget.hide()
            self.action_refresh_aggregate.setEnabled(False)
            self.action_calibrate.setEnabled(False)
            self.action_inflate.setEnabled(False)

    def reset_aggregate(self):
        '''
        Clear all pointers to the survey data to allow its garbage collection
        '''
        self.survey_simulation.clear()
#        for widget in self.aggregate_widgets:
#            widget.clear()
        self._explore_data_widget.clear()
        self._aggregate_output_widget.clear()
        gc.collect()

    def calibrate(self):
        '''
        Launch Calibration widget
        '''
        # liberate some memory before loading new data
        calibration = CalibrationWidget(inputs = self.simualtion_survey.survey, 
                                        outputs = self.simualtion_survey.outputs, parent = self)
        calibration.exec_()
        
    def inflate(self):
        '''
        Launch Calibration widget
        '''
        inflation = InflationWidget(inputs = self.simualtion_survey.survey, parent = self)
        inflation.exec_()
                
    def modeReforme(self, b):
        self.reforme = b
        self.scenario_simulation.set_config(reforme = self.reforme)
        self.survey_simulation.set_config(reforme = self.reforme)
        self.changed_bareme()
        self.changed_aggregate()

    def modeBareme(self):
        self.mode = 'bareme'
        nmen = CONF.get('simulation', 'nmen')
        if nmen == 1: CONF.set('simulation', 'nmen', 101)
        self.scenario_simulation.set_config(nmen = 101, mode = self.mode)
        self.changed_bareme()

    def modeCasType(self):
        self.mode = 'castype'
        self.scenario_simulation.set_config(nmen = 1, mode = self.mode)
        CONF.set('simulation', 'nmen', 1)
        self.changed_bareme()

    def refresh_bareme(self):
        # Consistency check on scenario
        msg = self.scenario_simulation.scenario.check_consistency()
        if msg:
            QMessageBox.critical(self, u"Ménage non valide",
                                 msg, 
                                 QMessageBox.Ok, QMessageBox.NoButton)
            return False
        # If it is consistent starts the computation
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.statusbar.showMessage(u"Calcul (mode barème) en cours...")
        self.action_refresh_bareme.setEnabled(False)
        # set the table model to None before changing data
        self._table.clearModel()
        
        data, data_default = self.scenario_simulation.compute()
        self._table.updateTable(data, self.scenario_simulation, dataDefault = data_default)
        self._graph.updateGraph(data, self.scenario_simulation, dataDefault = data_default)

        self.statusbar.showMessage(u"")
        QApplication.restoreOverrideCursor()

    
    def refresh_aggregate(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        self.statusbar.showMessage(u"Calcul des aggrégats en cours, ceci peut prendre quelques minutes...")
        self.action_refresh_aggregate.setEnabled(False)

        self._aggregate_output_widget.clear()
        self._explore_data_widget.clear()
        self.survey_simulation.clear()

        gc.collect()
        self.survey_simulation.compute()
        print 'Refreshing aggregates'
        agg = Aggregates()
        agg.set_simulation(self.survey_simulation)
        agg.compute()
        dist = OFPivotTable()
        dist.set_simulation(self.survey_simulation)
        self.refresh_dataframes()
        
        # Compute aggregates
        self._aggregate_output_widget.set_aggregates(agg)
        self._aggregate_output_widget.refresh_plugin()
        self._distribution_widget.set_of_pivot_table(dist)
        self._distribution_widget.refresh_plugin()
        #self._distribution_widget.update_view(data, descriptions = descr, default = data_default)
        
        self.statusbar.showMessage(u"")
        QApplication.restoreOverrideCursor()


    def refresh_dataframes(self):
        '''
        Populates dataframes in dataframe_widget
        '''
        self._explore_data_widget.set_year(self.survey_simulation.survey.survey_year)
        self._explore_data_widget.add_dataframe(self.survey_simulation.survey.table, name = "input")
        if self.survey_simulation.outputs is not None:
            self._explore_data_widget.add_dataframe(self.survey_simulation.outputs.table, name = "output")
        if self.reforme:
            if self.survey_simulation.outputs_default is not None:
                self._explore_data_widget.add_dataframe(self.survey_simulation.outputs_default.table, name = "output_default")

    
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

    def apply_settings(self):
        '''
        Use settings from configuration files
        '''
        
        # General settings
        country = CONF.get('simulation', 'country')
        year = CONF.get('simulation', 'datesim').year
        bareme_only = CONF.get('paths', 'survey_data/bareme_only')         
        
        # Sceanrio settings   
        self.XAXIS = CONF.get('simulation', 'xaxis')
        nmen = CONF.get('simulation', 'nmen')
        maxrev = CONF.get('simulation', 'maxrev')

        if not bareme_only:
            self.survey_simulation.set_config(year = year, country = country, reforme = self.reforme)
            self.survey_simulation.set_param()

        self.scenario_simulation.set_config(year = year, country = country, xaxis = self.XAXIS, 
                                            nemn = nmen, maxrev = maxrev, reforme = False, mode ='bareme')
        self.scenario_simulation.set_param()
        
        """Apply settings changed in 'Preferences' dialog box"""
        if self.isLoaded == True:
            self._parametres.initialize()
            self.refresh_bareme()                
        if self.calibration_enabled:
            self.action_calibrate.setEnabled(True)
        if self.inflation_enabled:
            self.action_inflate.setEnabled(True)
        if self.aggregate_enabled:
            self.enable_aggregate(True)

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

    def changed_bareme(self):
        self.statusbar.showMessage(u"Appuyez sur F9 pour lancer la simulation")
        self.action_refresh_bareme.setEnabled(True)
    
    def changed_param(self):
        P, P_default = self._parametres.getParam(), self._parametres.getParam(defaut = True) 
        self.statusbar.showMessage(u"Appuyez sur F9/F10 pour lancer la simulation")
        self.scenario_simulation.set_param(P, P_default)
        self.action_refresh_bareme.setEnabled(True)
        if self.aggregate_enabled:
            self.survey_simulation.set_param(P, P_default)
            self.action_refresh_aggregate.setEnabled(True)
          
    def changed_aggregate(self):
        self.statusbar.showMessage(u"Appuyez sur F10 pour lancer la simulation")
        if self.aggregate_enabled:
            self.action_refresh_aggregate.setEnabled(True)
            
    def calculated(self):
        self.statusbar.showMessage(u"Aggrégats calculés")
        self.emit(SIGNAL('aggregate_calculated()'))
        self.action_refresh_aggregate.setEnabled(False)
        self._inequality_widget.set_data(self.survey_simulation.outputs)
        self._inequality_widget.refresh()
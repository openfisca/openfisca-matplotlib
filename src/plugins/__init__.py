# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# This file is inspired by Spyder, see openfisca/spyder.txt for more details


"""
src.plugins
=================

Here, 'plugins' are widgets designed specifically for Openfisca
These plugins inherit the following classes
(OpenfiscaPluginMixin & OpenfiscaPluginWidget)
"""

from src.gui.qt.QtGui import (QDockWidget, QWidget, QShortcut, QCursor,
                                QKeySequence, QMainWindow, QApplication)
from src.gui.qt.QtCore import SIGNAL, Qt, QObject
from src.gui.qt.QtCore import pyqtSignal as Signal

# Local imports

from src.gui.utils.qthelpers import toggle_actions
from src.gui.config import CONF
from src.gui.userconfig import NoDefault

from src.gui.guiconfig import get_font, set_font, get_icon
from src.plugins.general.configdialog import OpenfiscaConfigPage
  
get_font = None
set_font = None
get_icon = None
OpenficsConfigPage = object

class PluginConfigPage(OpenfiscaConfigPage):
    """
    Plugin configuration dialog box page widget
    """
    def __init__(self, plugin, parent):
        self.plugin = plugin
        self.get_option = plugin.get_option
        self.set_option = plugin.set_option
        self.get_name = plugin.get_plugin_title
        self.get_icon = plugin.get_plugin_icon
        self.get_font = plugin.get_plugin_font
        self.set_font = plugin.set_plugin_font
        self.apply_settings = plugin.apply_plugin_settings
        OpenfiscaConfigPage.__init__(self, parent)


class OpenfiscaPluginMixin(object):
    """
    Useful methods to bind widgets to the main window
    See OpenfiscaPluginWidget class for required widget interface
    
    Signals:
        sig_option_changed
            Example:
            plugin.sig_option_changed.emit('show_all', checked)
        'show_message(QString,int)'
    """
    CONF_SECTION = None
    CONFIGWIDGET_CLASS = None
    ALLOWED_AREAS = Qt.AllDockWidgetAreas
    LOCATION = Qt.LeftDockWidgetArea
    FEATURES = QDockWidget.DockWidgetClosable | \
               QDockWidget.DockWidgetFloatable | \
               QDockWidget.DockWidgetMovable
    DISABLE_ACTIONS_WHEN_HIDDEN = True
    sig_option_changed = None

    def __init__(self, main):
        """
        Bind widget to a QMainWindow instance
        """
        super(OpenfiscaPluginMixin, self).__init__()
        assert self.CONF_SECTION is not None
        self.main = main
        self.default_margins = None
        self.plugin_actions = None
        self.dockwidget = None
        self.mainwindow = None
        self.ismaximized = False
        self.isvisible = False
        
    def initialize_plugin(self):
        """
        Initialize plugin: connect signals, setup actions, ...
        """
        self.plugin_actions = self.get_plugin_actions()
        QObject.connect(self, SIGNAL('show_message(QString,int)'),
                        self.show_message)
        QObject.connect(self, SIGNAL('update_plugin_title()'),
                        self.__update_plugin_title)
        if self.sig_option_changed is not None:
            self.sig_option_changed.connect(self.set_option)
        self.setWindowTitle(self.get_plugin_title())
        
    def update_margins(self):
        layout = self.layout()
        if self.default_margins is None:
            self.default_margins = layout.getContentsMargins()
        if CONF.get('main', 'use_custom_margin', True):
            margin = CONF.get('main', 'custom_margin', 0)
            layout.setContentsMargins(*[margin]*4)
        else:
            layout.setContentsMargins(*self.default_margins)
            
    def __update_plugin_title(self):
        """
        Update plugin title, i.e. dockwidget or mainwindow title
        """
        if self.dockwidget is not None:
            win = self.dockwidget
        elif self.mainwindow is not None:
            win = self.mainwindow
        else:
            return
        win.setWindowTitle(self.get_plugin_title())
        
    def create_dockwidget(self):
        """
        Add to parent QMainWindow as a dock widget
        """

        # This is not clear yet why the following do not work...
        # (see Issue #880)
##         # Using Qt.Window window flags solves Issue #880 (detached dockwidgets
##         # are not painted after restarting Spyder and restoring their hexstate)
##         # but it does not work with PyQt <=v4.7 (dockwidgets can't be docked)
##         # or non-Windows platforms (lot of warnings are printed out)
##         # (so in those cases, we use the default window flags: Qt.Widget):
##         flags = Qt.Widget if is_old_pyqt or os.name != 'nt' else Qt.Window
        dock = QDockWidget(self.get_plugin_title(), self.main)#, flags)

        dock.setObjectName(self.__class__.__name__+"_dw")
        dock.setAllowedAreas(self.ALLOWED_AREAS)
        dock.setFeatures(self.FEATURES)
        dock.setWidget(self)
        self.update_margins()
        self.connect(dock, SIGNAL('visibilityChanged(bool)'),
                     self.visibility_changed)
        self.dockwidget = dock
        short = self.get_option("shortcut", None)
        if short is not None:
            shortcut = QShortcut(QKeySequence(short),
                                 self.main, self.switch_to_plugin)
            self.register_shortcut(shortcut, "_",
                                   "Switch to %s" % self.CONF_SECTION,
                                   default=short)
        return (dock, self.LOCATION)
    
    
    def create_configwidget(self, parent):
        """
        Create configuration dialog box page widget
        """
        if self.CONFIGWIDGET_CLASS is not None:
            configwidget = self.CONFIGWIDGET_CLASS(self, parent)
            configwidget.initialize()
            return configwidget

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        raise NotImplementedError
    
    def register_shortcut(self, qaction_or_qshortcut, context, name,
                          default=NoDefault):
        """
        Register QAction or QShortcut to OF main application,
        with shortcut (context, name, default)
        """
        self.main.register_shortcut(qaction_or_qshortcut,
                                    context, name, default)
        
    def register_widget_shortcuts(self, context, widget):
        """
        Register widget shortcuts
        widget interface must have a method called 'get_shortcut_data'
        """
        for qshortcut, name, default in widget.get_shortcut_data():
            self.register_shortcut(qshortcut, context, name, default)
    
    def switch_to_plugin(self):
        """
        Switch to plugin
        This method is called when pressing plugin's shortcut key
        """
        if not self.ismaximized:
            self.dockwidget.show()
        self.visibility_changed(True)

    def visibility_changed(self, enable):
        """
        DockWidget visibility has changed
        """
        if enable:
            self.dockwidget.raise_()
            widget = self.get_focus_widget()
            if widget is not None:
                widget.setFocus()
        visible = self.dockwidget.isVisible() or self.ismaximized
        if self.DISABLE_ACTIONS_WHEN_HIDDEN:
            toggle_actions(self.plugin_actions, visible)
        # if visible:
            # self.refresh_plugin() #XXX Is it a good idea?
        self.isvisible = enable and visible

    def set_option(self, option, value):
        """
        Set a plugin option in configuration file
        Use a SIGNAL to call it, e.g.:
        plugin.sig_option_changed.emit('show_all', checked)
        """
        CONF.set(self.CONF_SECTION, str(option), value)

    def get_option(self, option, default=NoDefault):
        """
        Get a plugin option from configuration file
        """
        return CONF.get(self.CONF_SECTION, option, default)
    
    def get_plugin_font(self, option=None):
        """
        Return plugin font option
        """
        return get_font(self.CONF_SECTION, option)
    
    def set_plugin_font(self, font, option=None):
        """
        Set plugin font option
        """
        set_font(font, self.CONF_SECTION, option)
        
    def show_message(self, message, timeout=0):
        """
        Show message in main window's status bar
        """
        self.main.statusBar().showMessage(message, timeout)

    def starting_long_process(self, message):
        """
        Showing message in main window's status bar
        and changing mouse cursor to Qt.WaitCursor
        """
        self.show_message(message)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
    def ending_long_process(self, message=""):
        """
        Clearing main window's status bar
        and restoring mouse cursor
        """
        QApplication.restoreOverrideCursor()
        self.show_message(message, timeout=2000)
        QApplication.processEvents()
        
    def set_default_color_scheme(self, name='Spyder'):
        """Set default color scheme (only once)"""
        color_scheme_name = self.get_option('color_scheme_name', None)
        if color_scheme_name is None:
            names = CONF.get("color_schemes", "names")
            if name not in names:
                name = names[0]
            self.set_option('color_scheme_name', name)


class OpenfiscaPluginWidget(QWidget, OpenfiscaPluginMixin):
    """
    OpenFisca base widget class
    OpenFisca's widgets either inherits this class or re-implements its interface
    """
    sig_option_changed = Signal(str, object)
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        OpenfiscaPluginMixin.__init__(self, parent)
        
    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        raise NotImplementedError
    
    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see OpenfiscaPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')
    
    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        pass
        
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        raise NotImplementedError
        
    def refresh_plugin(self):
        """
        Refresh widget
        """
        raise NotImplementedError
    
    def get_plugin_actions(self):
        """
        Return a list of actions related to plugin
        Note: these actions will be enabled when plugin's dockwidget is visible
              and they will be disabled when it's hidden
        """
        raise NotImplementedError
    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window"""
        raise NotImplementedError

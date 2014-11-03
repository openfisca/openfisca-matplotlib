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


from __future__ import division

import locale
import os

from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrow
from matplotlib.ticker import FuncFormatter
import numpy as np

#from openfisca_core import model

from ...gui.baseconfig import get_translation
from ...gui.config import get_icon
from ...gui.qt.compat import (to_qvariant, getsavefilename)
from ...gui.qt.QtCore import (
    QAbstractItemModel, QModelIndex, Qt, SIGNAL, QSize, QString,
    )
from ...gui.qt.QtGui import (
    QColor, QVBoxLayout, QDialog, QMessageBox, QTreeView, QIcon, QPixmap, QHBoxLayout, QPushButton,
    )
from ...gui.utils.qthelpers import create_action
from ...gui.views.ui_graph import Ui_Graph
from .. import OpenfiscaPluginWidget
from ..utils import OutNode


_ = get_translation('openfisca_qt')
locale.setlocale(locale.LC_ALL, '')


class GraphFormater(QDialog):
    def __init__(self, data, mode, parent = None):
        super(GraphFormater, self).__init__(parent)
        self.setObjectName(u'Affichage')
        self.setWindowTitle(u'Options du graphique')
        self.data = data
        self.parent = parent
        view = QTreeView(self)
        view.setIndentation(10)
        self.model = DataModel(data, mode, self)
        view.setModel(self.model)
        VLayout = QVBoxLayout()
        HLayout = QHBoxLayout()
        allBtn = QPushButton(u'Tout cocher')
        noneBtn = QPushButton(u'Tout décocher')
        HLayout.addWidget(allBtn)
        HLayout.addWidget(noneBtn)
        self.setLayout(VLayout)
        VLayout.addLayout(HLayout)
        VLayout.addWidget(view)
        self.connect(self.model, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.updateGraph)
        self.connect(allBtn, SIGNAL('clicked()'), self.checkAll)
        self.connect(noneBtn, SIGNAL('clicked()'), self.checkNone)


    def checkAll(self):
        self.data.setLeavesVisible()
        self.updateGraph()
        self.model.reset()

    def checkNone(self):
        self.data.hideAll()
        self.updateGraph()
        self.model.reset()

    def updateGraph(self):
        self.parent.updateGraph2()

def colorIcon(color):
    r, g, b = color
    qcolor = QColor(r, g, b)
    size = QSize(22,22)
    pixmap = QPixmap(size)
    pixmap.fill(qcolor)
    return QIcon(pixmap)

class DataModel(QAbstractItemModel):
    def __init__(self, root, mode, parent=None):
        super(DataModel, self).__init__(parent)
        self._rootNode = root
        self.mode = mode

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = self.getNode(parent)
        return parentNode.childCount()

    def columnCount(self, parent):
        return 1

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return to_qvariant(node.desc)
        if role == Qt.DecorationRole:
            return colorIcon(node.color)
        if role == Qt.CheckStateRole:
            return to_qvariant(2*(node.visible>=1))


    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        if role == Qt.CheckStateRole:
            if not(node.parent == self._rootNode):
                first_index = self.createIndex(node.parent.row(), 0, node.parent)
            else:
                first_sibling = node.parent.children[0]
                first_index = self.createIndex(first_sibling.row(), 0, first_sibling)
            last_sibling = node.parent.children[-1]
            last_index = self.createIndex(last_sibling.row(), 0, last_sibling)
            if self.mode == 'bareme':
                if node.visible>=1: node.visible = 0
                else: node.visible = 1
            else:
                if node.visible>=1: node.setHidden()
                else: node.setVisible()
            self.dataChanged.emit(first_index, last_index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if   section == 0: return u"Variable"

    def flags(self, index):
        node = self.getNode(index)
        if np.any(node.vals != 0):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsSelectable

    """Should return the parent of the node with the given QModelIndex"""
    def parent(self, index):
        node = self.getNode(index)
        parentNode = node.parent
        if parentNode == self._rootNode:
            return QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    """Should return a QModelIndex that corresponds to the given row, column and parent node"""
    def index(self, row, column, parent):
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._rootNode

class ScenarioGraphWidget(OpenfiscaPluginWidget, Ui_Graph):
    """
    Scenario Graph Widget
    """
    CONF_SECTION = 'composition'

    def __init__(self, parent = None):
        super(ScenarioGraphWidget, self).__init__(parent)
        self.setupUi(self)
        self._parent = parent
        self.mplwidget.mpl_connect('pick_event', self.on_pick)
        self.mplwidget.mpl_connect('motion_notify_event', self.pick)
        self.connect(self.option_btn, SIGNAL('clicked()'), self.set_option)
        self.connect(self.taux_btn, SIGNAL('stateChanged(int)'), self.set_taux)
        self.connect(self.hidelegend_btn, SIGNAL('toggled(bool)'), self.hide_legend)
        self.taux = False
        self.legend = True
        self.simulation = None

        self.setLayout(self.verticalLayout)
        self.initialize_plugin()

    #------ Public API ---------------------------------------------

    def set_taux(self, value):
        """
        Switch on/off the tax rates view

        Parameters
        ----------

        value : bool
                If True, switch to tax rates view

        """
        if value: self.taux = True
        else: self.taux = False
        self.updateGraph2()

    def hide_legend(self, value):
        if value: self.legend = False
        else: self.legend = True
        self.updateGraph2()

    def set_option(self):
        '''
        Sets graph options
        '''
        try:
            mode = self.simulation.mode
        except:
            mode = 'bareme'

        gf = GraphFormater(self.data, mode, self)
        gf.exec_()

    def pick(self, event):
        if not event.xdata is None and not event.ydata is None:
            self.mplwidget.figure.pick(event)
        else:
            self.setToolTip("")

    def on_pick(self, event):
        label = event.artist._label
        self.setToolTip(label)

    def updateGraph(self, scenario):
        """
        Update the graph according to simulation
        """
        self.scenario = scenario
        print scenario
        # TODO: link the decompsotion with parameters
        data = OutNode.create_from_scenario_decomposition_json(
            scenario = scenario,
            simulation = None,
            decomposiiton_json = None
            )

        dataDefault = data # TODO: data_default
        reforme = scenario.reforme = False # TODO: fix this
        mode = scenario.mode = "castype" # TODO: "castype" ou "bareme"
        x_axis = scenario.x_axis = "sal" # TODO change this too
        self.data = data
        self.dataDefault = dataDefault
        self.data.setLeavesVisible()

        data['revdisp'].visible = 1
        if mode == 'bareme':  # TODO: make this country-totals specific
            for rev in ['salsuperbrut', 'salbrut', 'chobrut', 'rstbrut']:
                try:
                    data[rev].setHidden()
                except:
                    pass
            if reforme:
                data.hideAll()

        self.populate_absBox(x_axis, mode)

        for axe in self.main.composition.XAXIS_PROPERTIES.itervalues():

            if axe['name'] == x_axis:
                self.graph_x_axis = axe['typ_tot_default']
                break
        self.updateGraph2()

    def updateGraph2(self):

        ax = self.mplwidget.axes
        ax.clear()
        currency = self.main.tax_benefit_system.CURRENCY
        mode = self.scenario.mode
        reforme = self.scenario.reforme

        if mode == 'castype':
            drawWaterfall(self.data, ax)
        else:
            if self.taux:
                drawTaux(self.data, ax, self.graph_x_axis, reforme, self.dataDefault)
            else:
                drawBareme(self.data, ax, self.graph_x_axis, reforme, self.dataDefault, self.legend, currency = currency)

        self.mplwidget.draw()

    def populate_absBox(self, x_axis, mode):
        self.disconnect(self.absBox, SIGNAL('currentIndexChanged(int)'), self.x_axis_changed)
        self.absBox.clear()
        if mode == 'castype':
            self.absBox.setEnabled(False)
            self.taux_btn.setEnabled(False)
            self.hidelegend_btn.setEnabled(False)
            return

        self.taux_btn.setEnabled(True)
        self.absBox.setEnabled(True)
        self.hidelegend_btn.setEnabled(True)

        for axe in model.x_axes.itervalues():
            if axe.name == x_axis:
                typ_revs_labels = axe.typ_tot.values()
                typ_revs = axe.typ_tot.keys()
                self.absBox.addItems(typ_revs_labels) # TODO: get label from description
                self.absBox.setCurrentIndex(typ_revs.index(axe.typ_tot_default))
                self.connect(self.absBox, SIGNAL('currentIndexChanged(int)'), self.x_axis_changed)
                return

    def x_axis_changed(self):
        mode = self.simulation.mode
        if mode == "bareme":
            text =  self.absBox.currentText()
            for axe in self.main.composition.XAXIS_PROPERTIES.itervalues():
                for key, label in axe.typ_tot.iteritems():
                    if text == label:
                        self.graph_x_axis = key
                        self.updateGraph2()
                        return

    def save_figure(self, *args):
        filetypes = self.mplwidget.get_supported_filetypes_grouped()
        sorted_filetypes = filetypes.items()
        sorted_filetypes.sort()
        default_filetype = self.mplwidget.get_default_filetype()

        output_dir = self.get_option('graph/export_dir')
        start = os.path.join(output_dir, 'image.') + default_filetype
        filters = []
        selectedFilter = None
        for name, exts in sorted_filetypes:
            exts_list = " ".join(['*.%s' % ext for ext in exts])
            filtre = '%s (%s)' % (name, exts_list)
            if default_filetype in exts:
                selectedFilter = filtre
            filters.append(filtre)
        filters = ';;'.join(filters)


        fname, format = getsavefilename(
            self, _("Save image"), start, filters, selectedFilter) # "Enregistrer l'image"

        if fname:
            output_dir = os.path.dirname(str(fname))
            self.main.composition.set_option('graph/export_dir', output_dir)
            try:
                self.mplwidget.print_figure( fname )
            except Exception, e:
                QMessageBox.critical(
                    self, _("Error when saving image"), str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)


    #------ OpenfiscaPluginMixin API ---------------------------------------------
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return _("Test case graphic")


    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see OpenfiscaPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')

    def get_plugin_actions(self):
        """
        Return a list of actions related to plugin
        Note: these actions will be enabled when plugin's dockwidget is visible
              and they will be disabled when it's hidden
        """
        self.save_action = create_action(
            self, _("Save &graph"),
            icon = 'filesave.png',
            tip = _("Save test case graph"),
            triggered = self.save_figure
            )
        self.register_shortcut(
            self.save_action,
            context = "Graph",
            name =_("Save test case graph"),
            default = "Ctrl+G"
            )
        self.file_menu_actions = [self.save_action]
        self.main.file_menu_actions += self.file_menu_actions

        return self.file_menu_actions

    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.main.add_dockwidget(self)

    def refresh_plugin(self):
        '''
        Update Graph
        '''
        self.updateGraph(self.main.scenario)

    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True


def draw_simulation_bareme(simulation, ax, graph_x_axis = None, legend = False, position = 1):
    """
    Draws a bareme on matplotlib.axes.Axes
    """
    reforme = simulation.reforme
    alter = (simulation.alternative_scenario is not None)
    currency = self.main.tax_benefit_system.CURRENCY
    simulation.compute()
    data = simulation.data
    data_default = simulation.data_default

    data.setLeavesVisible()
    data_default.setLeavesVisible()
    if graph_x_axis is None:
        graph_x_axis = 'sal'
    if not alter:
        drawBareme(data, ax, graph_x_axis, reforme, data_default, legend, currecncy = currency)
    else:
        drawBaremeCompareHouseholds(data, ax, graph_x_axis, data_default, legend, currecny = currency, position = position)


def draw_simulation_taux(simulation, ax, graph_x_axis = None, legend = True):
    """
    Draws a bareme on matplotlib.axes.Axes object ax
    """
    reforme = simulation.reforme or (simulation.alternative_scenario is not None)
    simulation.compute()
    data, data_default = simulation.data, simulation.data_default

    data.setLeavesVisible()
    data_default.setLeavesVisible()
    if graph_x_axis is None:
        graph_x_axis = 'sal'
    drawTaux(data, ax, graph_x_axis, reforme, data_default, legend = legend)


def draw_simulation_waterfall(simulation, ax):
    """
    Draws a waterfall on matplotlib.axes.Axes object ax
    """
    data, data_default = simulation.compute()
    del data_default
    data.setLeavesVisible()
    drawWaterfall(data, ax)


def drawWaterfall(data, ax, currency = None):

    ax.figure.subplots_adjust(bottom = 0.15, right = 0.95, top = 0.95, left = 0.1)
    barwidth = 0.8
    number = [0]
    patches = []
    codes = []
    shortnames = []

    def drawNode(node, prv):
        prev = prv + 0
        val = node.vals[0]
        bot = prev
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals[0]
        if (val != 0) and node.visible:
            r, g, b = node.color
            arrow = FancyArrow(
                number[0] + barwidth / 2, bot, 0, val,
                width = barwidth,
                fc = (r / 255, g / 255, b / 255), linewidth = 0.5, edgecolor = 'black',
                label = node.desc, picker = True, length_includes_head = True,
                head_width = barwidth,
                head_length = abs(val / 15),
                )
            arrow.top = bot + max(0, val)
            arrow.absci = number[0] + 0
#            a = Rectangle((number[0], bot), barwidth, val, fc = node.color, linewidth = 0.5, edgecolor = 'black', label = node.desc, picker = True)
            arrow.value = round(val)
            patches.append(arrow)
            codes.append(node.code)
            shortnames.append(node.shortname)
            number[0] += 1

    prv = 0
    drawNode(data, prv)
    for patch in patches:
        ax.add_patch(patch)

    n = len(patches)
    abscisses = np.arange(n)
    xlim = (- barwidth * 0.5, n - 1 + barwidth * 1.5)
    ax.hold(True)
    ax.plot(xlim, [0, 0], color = 'black')
    ax.set_xticklabels(shortnames, rotation = '45')
    ax.set_xticks(abscisses + barwidth / 2)
    ax.set_xlim((-barwidth / 2, n - 1 + barwidth * 1.5))
    ticks = ax.get_xticklines()
    for tick in ticks:
        tick.set_visible(False)

    for rect in patches:
        x = rect.absci
        y = rect.top
        val = u'{} {}'.format(int(rect.value), currency)
        width = barwidth
        if rect.value >= 0:
            col = 'black'
        else:
            col = 'red'
        ax.text(x + width / 2, y + 1, val, horizontalalignment = 'center',
                verticalalignment = 'bottom', color= col, weight = 'bold')
    m, M = ax.get_ylim()
    ax.set_ylim((m, 1.05 * M))


def drawBareme(data, axes, x_axis, reform = False, reference_data = None, legend = True, currency = None):
    '''
    Draws bareme
    '''
    if reference_data is None:
        reference_data = data
    axes.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
    if reform:
        prefix = 'Variation '
    else:
        prefix = ''
    axes.hold(True)
    x_axis_data = reference_data[x_axis]
    n_points = len(x_axis_data.vals)
    xlabel = x_axis_data.desc
    axes.set_xlabel(xlabel)
    axes.set_ylabel(prefix + u"{} ({} par an)".format(data.code, currency))
    axes.set_xlim(np.amin(x_axis_data.vals), np.amax(x_axis_data.vals))
    if not reform:
        axes.set_ylim(np.amin(x_axis_data.vals), np.amax(x_axis_data.vals))
    axes.plot(x_axis_data.vals, np.zeros(n_points), color = 'black', label = 'x_axis')

    def drawNode(node, prv):
        prev = prv + 0
        if np.any(node.vals != 0) and node.visible:
            r, g, b = node.color
            col = (r / 255, g / 255, b / 255)
            if node.typevar == 2:
                a = axes.plot(
                    x_axis_data.vals,
                    node.vals,
                    color = col,
                    linewidth = 2,
                    label = prefix + node.desc,
                    )
            else:
                a = axes.fill_between(
                    x_axis_data.vals,
                    prev + node.vals,
                    prev,
                    color = col,
                    linewidth = 0.2,
                    edgecolor = 'black',
                    picker = True,
                    )
                a.set_label(prefix + node.desc)
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals

    prv = np.zeros(n_points)
    drawNode(data, prv)
    if legend:
        createLegend(axes)


def drawBaremeCompareHouseholds(data, ax, x_axis, dataDefault = None, legend = True , currency = "", position = 2):
    '''
    Draws bareme
    '''
    if dataDefault is None:
        raise Exception('drawBaremeCompareHouseHolds: dataDefault must be defined')

    ax.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
    prefix = 'Variation '
    ax.hold(True)
    xdata = dataDefault[x_axis]
    NMEN = len(xdata.vals)
    xlabel = xdata.desc
    ax.set_xlabel(xlabel)
    ax.set_ylabel(prefix + u"Revenu disponible (" + currency + " par an)")
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    ax.plot(xdata.vals, np.zeros(NMEN), color = 'black', label = 'x_axis')
    code_list = ['af', 'cf', 'ars', 'rsa', 'aefa', 'psa', 'logt', 'irpp', 'ppe', 'revdisp']

    def drawNode(node, prv):
        minimum = 0
        maximum = 0
        prev = prv + 0
#        if np.any(node.vals != 0) and node.visible and node.code != 'root' and node.code in code_list:
        if np.any(node.vals != 0) and node.code != 'root' and node.code in code_list:
            node.visible = True
            r, g, b = node.color
            col = (r / 255, g / 255, b / 255)
            if node.typevar == 2:
                a = ax.plot(xdata.vals, node.vals, color = col, linewidth = 2, label = prefix + node.desc)
            else:
                a = ax.fill_between(xdata.vals, prev + node.vals, prev, color = col, linewidth = 0.2,
                                    edgecolor = 'black', picker = True)
                a.set_label(prefix + node.desc)
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals
            minimum = min([np.amin(prev), minimum])
            maximum = max([np.amax(prev), maximum])
        return minimum, maximum * 1.1

    prv = np.zeros(NMEN)
    minimum, maximum = drawNode(data, prv)
    ax.set_ylim(minimum, maximum)

    if legend:
        createLegend(ax, position = position)


def drawBaremeCompareHouseholds2(data, ax, x_axis, dataDefault = None, legend = True, currency = "", position = 2):
    '''
    Draws bareme
    '''
    if dataDefault is None:
        raise Exception('drawBaremeCompareHouseHolds: dataDefault must be defined')

    ax.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
    prefix = 'Variation '
    ax.hold(True)
    xdata = dataDefault[x_axis]
    NMEN = len(xdata.vals)
    xlabel = xdata.desc
    ax.set_xlabel(xlabel)
    ax.set_ylabel(prefix + u"Revenu disponible (" + currency + " par an)")
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    ax.plot(xdata.vals, np.zeros(NMEN), color = 'black', label = 'x_axis')
    node_list = ['af', 'cf', 'ars', 'rsa', 'aefa', 'psa', 'logt', 'irpp', 'ppe', 'revdisp']
    prv = np.zeros(NMEN)

    for nod in node_list:
        node = data[nod]
        prev = prv + 0
        r, g, b = node.color
        col = (r / 255, g / 255, b / 255)
        if node.typevar == 2:
            a = ax.plot(xdata.vals, node.vals, color = col, linewidth = 2, label = prefix + node.desc)
        else:
            a = ax.fill_between(xdata.vals, prev + node.vals, prev, color = col, linewidth = 0.2,
                                edgecolor = 'black', picker = True)
            a.set_label(prefix + node.desc)
        prv += node.vals

    if legend:
        createLegend(ax, position = position)


def percentFormatter(x, pos=0):
    return '%1.0f%%' % (x)


def drawTaux(data, ax, x_axis, reforme = False, dataDefault = None, legend = True):
    '''
    Draws marginal and average tax rates
    '''
    if dataDefault is None:
        dataDefault = data

    print "x_axis :", x_axis

    # TODO: the following is an ugly fix which is not general enough
    if x_axis == "rev_cap_brut":
        typ_rev = 'superbrut'
    elif x_axis == "rev_cap_net":
        typ_rev = 'net'
    elif x_axis == "fon":
        typ_rev = 'brut'
    else:
        for typrev, vars in model.REVENUES_CATEGORIES.iteritems():
            if x_axis in vars:
                typ_rev = typrev

    RB = RevTot(dataDefault, typ_rev)
    xdata = dataDefault[x_axis]

    RD = dataDefault['revdisp'].vals
    div = RB*(RB != 0) + (RB == 0)
    taumoy = (1 - RD / div) * 100
    taumar = 100 * (1 - (RD[:-1]-RD[1:]) / (RB[:-1]-RB[1:]))

    ax.hold(True)
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    ax.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    ax.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    ax.plot(xdata.vals, taumoy, label = u"Taux moyen d'imposition", linewidth = 2)
    ax.plot(xdata.vals[1:], taumar, label = u"Taux marginal d'imposition", linewidth = 2)
    ax.set_ylim(0,100)

    ax.yaxis.set_major_formatter(FuncFormatter(percentFormatter))
    if legend:
        createLegend(ax)


def createLegend(ax, position = 2):
    '''
    Creates legend
    '''
    p = []
    l = []
    for collec in ax.collections:
        if collec._visible:
            p.insert(0, Rectangle((0, 0), 1, 1, fc = collec._facecolors[0], linewidth = 0.5, edgecolor = 'black' ))
            l.insert(0, collec._label)
    for line in ax.lines:
        if line._visible and (line._label != 'x_axis'):
            p.insert(0, Line2D([0,1],[.5,.5],color = line._color))
            l.insert(0, line._label)
    ax.legend(p,l, loc= position, prop = {'size':'medium'})

def RevTot(data, typrev):
    '''
    Computes total revenues by type with definition is country specific
    '''
    dct = model.REVENUES_CATEGORIES
    first = True
    try:
        for var in dct[typrev]:
            if first:
                out = data[var].vals.copy() # WARNING: Copy is needed to avoid pointers problems (do not remove this line)!!!!
                first = False
            else:
                out += data[var].vals
        return out
    except:
        raise Exception("typrev is %s but typrev should be one of the following: %s" %(str(typrev), str(dct.keys())) )

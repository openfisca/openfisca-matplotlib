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
from Config import CONF
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant, SIGNAL, \
    QSize
from PyQt4.QtGui import QDockWidget, QFileDialog, QColor, QVBoxLayout, QDialog, \
    QMessageBox, QTreeView, QIcon, QPixmap, QHBoxLayout, QPushButton, QWidget, QAbstractItemView
from datetime import datetime
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrow
from matplotlib.ticker import FuncFormatter
from views.ui_graph import Ui_Graph
from core.qthelpers import OfTreeView
import csv
import os
import codecs
import cStringIO
import locale
import numpy as np
from core.utils import of_import

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
            return QVariant(node.desc)
        if role == Qt.DecorationRole:
            return colorIcon(node.color)
        if role == Qt.CheckStateRole:
            return QVariant(2*(node.visible>=1))
     
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

class Graph(QDockWidget, Ui_Graph):
    def __init__(self, parent = None):
        super(Graph, self).__init__(parent)
        self.setupUi(self)
        self._parent = parent
        self.mplwidget.mpl_connect('pick_event', self.on_pick)
        self.mplwidget.mpl_connect('motion_notify_event', self.pick)
        self.connect(self.option_btn, SIGNAL('clicked()'), self.set_option)
        self.connect(self.taux_btn, SIGNAL('stateChanged(int)'), self.set_taux)
        self.connect(self.hidelegend_btn, SIGNAL('toggled(bool)'), self.hide_legend)
        self.taux = False
        self.legend = True



    def set_taux(self, value):
        if value: self.taux = True
        else: self.taux = False
        self.updateGraph2()

    def hide_legend(self, value):
        if value: self.legend = False
        else: self.legend = True
        self.updateGraph2()
        
    def set_option(self):
        gf = GraphFormater(self.data, self.mode, self)
        gf.exec_()
    
    def pick(self, event):
        if not event.xdata is None and not event.ydata is None:
            self.mplwidget.figure.pick(event)
        else:
            self.setToolTip("")
    
    def on_pick(self, event):
        label = event.artist._label
        self.setToolTip(label)

    def updateGraph(self, data, reforme = False, mode = 'bareme', dataDefault = None):
        self.data = data
        self.dataDefault = dataDefault
        self.data.setLeavesVisible()
        self.reforme = reforme
        self.mode = mode
        data['revdisp'].visible = 1
        if self.mode == 'bareme':    # TODO make this country-totals specific
            if 'salsuperbrut' in data:
                data['salsuperbrut'].setHidden()
            if 'salbrut' in data:
                data['salbrut'].setHidden()
            if 'chobrut' in data:
                data['chobrut'].setHidden()
            if 'rstbrut' in data:
                data['rstbrut'].setHidden()
            if reforme:
                data.hideAll()
        
        self.xaxis = CONF.get('simulation', 'xaxis')
        self.populate_absBox(self.xaxis, self.mode)
        self.updateGraph2()
        
    def updateGraph2(self):
        ax = self.mplwidget.axes
        ax.clear()
        if self.mode == 'castype': drawWaterfall(self.data, ax)
        else:
            if self.taux:
                drawTaux(self.data, ax, self.xaxis, self.reforme, self.dataDefault)
            else:
                drawBareme(self.data, ax, self.xaxis, self.reforme, self.dataDefault, self.legend)

        self.mplwidget.draw()
    
    def populate_absBox(self, xaxis, mode):
        self.disconnect(self.absBox, SIGNAL('currentIndexChanged(int)'), self.xaxis_changed)
        self.absBox.clear()
        if mode == 'castype':
            self.absBox.setEnabled(False)
            self.taux_btn.setEnabled(False)
            self.hidelegend_btn.setEnabled(False)
            return
        
        self.taux_btn.setEnabled(True)
        self.absBox.setEnabled(True)
        self.hidelegend_btn.setEnabled(True)
        
        XAXES = of_import('utils', 'XAXES')
        for axis, vars in XAXES.iteritems():
            if axis == xaxis:
                self.absBox.addItems(vars[0])
                self.absBox.setCurrentIndex(vars[1])            
                self.connect(self.absBox, SIGNAL('currentIndexChanged(int)'), self.xaxis_changed)
                return

    def xaxis_changed(self):
        
        temp = {u'Salaire super brut': 'salsuperbrut',
                u'Salaire brut' : 'salbrut',
                u'Salaire imposable': 'sal',
                u'Salaire net': 'salnet',
                u'Chômage brut' : 'chobrut',
                u'Chômage imposable': 'cho',
                u'Chômage net': 'chonet',
                u'Retraite brut': 'rstbrut',
                u'Retraite imposable' : 'rst',
                u'Retraite nette': 'rstnet',
                u'Revenus du capital bruts': 'rev_cap',
                u'Revenus du capital nets':  'rev_cap_net'}  # TODO discriminate bewteen revenu de placement et revenu du patrimoine
        if self.mode == "bareme":
            self.xaxis = temp[unicode(self.absBox.currentText())]
            self.updateGraph2()
            
    def save_figure(self, *args):
        filetypes = self.mplwidget.get_supported_filetypes_grouped()
        sorted_filetypes = filetypes.items()
        sorted_filetypes.sort()
        default_filetype = self.mplwidget.get_default_filetype()
        output_dir = CONF.get('paths', 'output_dir')
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

        fname = QFileDialog.getSaveFileName(
            self, "Enregistrer l'image", start, filters, selectedFilter)
        

        if fname:
            CONF.set('paths', 'output_dir', os.path.dirname(str(fname)))
            try:
                self.mplwidget.print_figure( unicode(fname) )
            except Exception, e:
                QMessageBox.critical(
                    self, "Erreur en enregistrant le fichier", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)

def drawWaterfall(data, ax):

    ax.figure.subplots_adjust(bottom = 0.15, right = 0.95, top = 0.95, left = 0.1)
    barwidth = 0.8
    number = [0]
    patches = []

    codes  = []
    shortnames = []

    def drawNode(node, prv):
        if node.code == 'nivvie':
            return
        prev = prv + 0
        val = node.vals[0]
        bot = prev
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals[0]
        if (val != 0) and node.visible and node.code != 'root':
            r,g,b = node.color
            a = FancyArrow(number[0] + barwidth/2, bot , 0, val, width = barwidth,  
                           fc = (r/255,g/255,b/255), linewidth = 0.5, edgecolor = 'black', 
                           label = node.desc, picker = True, length_includes_head=True, 
                           head_width=barwidth, head_length=abs(val/15))
            a.top = bot + max(0,val)
            a.absci = number[0] + 0
#            a = Rectangle((number[0], bot), barwidth, val, fc = node.color, linewidth = 0.5, edgecolor = 'black', label = node.desc, picker = True)
            a.value = round(val)
            patches.append(a)
            codes.append(node.code)
            shortnames.append(node.shortname)
            number[0] += 1

    prv = 0
    
    drawNode(data, prv)

    for patch in patches:
        ax.add_patch(patch)
    
    n = len(patches)
    abscisses = np.arange(n) 

    xlim = (-barwidth*0.5,n-1+barwidth*1.5)
    ax.hold(True)
    ax.plot(xlim, [0,0], color = 'black')
    ax.set_xticklabels(shortnames, rotation = '45')
    ax.set_xticks(abscisses + barwidth/2)
    ax.set_xlim((-barwidth/2, n-1+barwidth*1.5))
    ticks = ax.get_xticklines()
    for tick in ticks:
        tick.set_visible(False)

    for rect in patches:
        x = rect.absci
        y = rect.top
        val = '%d' % rect.value
        width = barwidth
        if rect.value>=0: col = 'black'
        else: col = 'red'
        ax.text(x + width/2, y + 1, val, horizontalalignment='center',
                 verticalalignment='bottom', color= col, weight = 'bold')
    
    m, M = ax.get_ylim()
    ax.set_ylim((m, 1.05*M))
    
def drawBareme(data, ax, xaxis, reforme = False, dataDefault = None, legend = True):
    if dataDefault == None: dataDefault = data

    ax.figure.subplots_adjust(bottom = 0.09, top = 0.95, left = 0.11, right = 0.95)
        
    if reforme: prefix = 'Variation '
    else: prefix = ''

    ax.hold(True)

    xdata = dataDefault[xaxis]
    
    NMEN = len(xdata.vals)
    xlabel = xdata.desc

    ax.set_xlabel(xlabel)
    ax.set_ylabel(prefix + u"Revenu disponible (€ par an)")
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    if not reforme:
        ax.set_ylim(np.amin(xdata.vals), np.amax(xdata.vals))
    
    ax.plot(xdata.vals, np.zeros(NMEN), color = 'black', label = 'xaxis')
    
    def drawNode(node, prv):
        prev = prv + 0
        if np.any(node.vals != 0) and node.visible and node.code != 'root':
            r,g,b = node.color
            col = (r/255, g/255, b/255)
            if node.typevar == 2:
                a = ax.plot(xdata.vals, node.vals, color = col, linewidth = 2, label = prefix + node.desc)
            else:
                a = ax.fill_between(xdata.vals, prev + node.vals, prev, color = col, linewidth = 0.2, edgecolor = 'black', picker = True)
                a.set_label(prefix + node.desc)
        for child in node.children:
            drawNode(child, prev)
            prev += child.vals

    prv = np.zeros(NMEN)

    drawNode(data, prv)

    if legend:
        createLegend(ax)

def percentFormatter(x, pos=0):
    return '%1.0f%%' %(x)

def drawTaux(data, ax, xaxis, reforme = False, dataDefault = None):
    if dataDefault == None: dataDefault = data
    
    REV_TYPE = of_import('utils', 'REV_TYPE')
    
    for typ_rev, vars in REV_TYPE.iteritems():
        if xaxis in vars:
            RB = RevTot(dataDefault, typ_rev)

    xdata = dataDefault[xaxis]
    RD = dataDefault['revdisp'].vals
    div = RB*(RB != 0) + (RB == 0)
    taumoy = (1 - RD/div)*100
    taumar = 100*(1 - (RD[:-1]-RD[1:])/(RB[:-1]-RB[1:]))

    ax.hold(True)
    ax.set_xlim(np.amin(xdata.vals), np.amax(xdata.vals))
    ax.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    ax.set_ylabel(r"$\left(1 - \frac{RevDisponible}{RevInitial} \right)\ et\ \left(1 - \frac{d (RevDisponible)}{d (RevInitial)}\right)$")
    ax.plot(xdata.vals, taumoy, label = u"Taux moyen d'imposition", linewidth = 2)
    ax.plot(xdata.vals[1:], taumar, label = u"Taux marginal d'imposition", linewidth = 2)
    ax.set_ylim(0,100)
    
    ax.yaxis.set_major_formatter(FuncFormatter(percentFormatter))
    createLegend(ax)

    
def createLegend(ax):
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
        if line._visible and (line._label != 'xaxis'):
            p.insert(0, Line2D([0,1],[.5,.5],color = line._color))
            l.insert(0, line._label)
    ax.legend(p,l, loc= 2, prop = {'size':'medium'})

def RevTot(data, typrev):
    '''
    Computes total revenues by type with definition is country specific
    '''
    REV_TYPE = of_import('utils', 'REV_TYPE')
    dct = REV_TYPE
    first = True
    if typrev in dct:
        for var in dct[typrev]:
            if first:
                out = data[var].vals
                first = False
            else:
                out += data[var].vals
        return out 
    else:
        raise Exception("typrev should be one of the following: " + str(REV_TYPE.keys()))
    




class OutTable(QDockWidget):
    def __init__(self, parent = None):
        super(OutTable, self).__init__(parent)
        self.setObjectName("Table")
        self.setWindowTitle("Table")
        self.dockWidgetContents = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.treeView = OfTreeView(self.dockWidgetContents)
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setIndentation(10)
        selection_behavior = QAbstractItemView.SelectRows
        # we should enable contguous selection, but the copy method does not yet handle this.
#        selection_mode = QAbstractItemView.ContiguousSelection
        selection_mode = QAbstractItemView.SingleSelection       
        self.treeView.setSelectionBehavior(selection_behavior)
        self.treeView.setSelectionMode(selection_mode)
        self.verticalLayout.addWidget(self.treeView)
        self.setWidget(self.dockWidgetContents)

    def clearModel(self):
        self.treeView.setModel(None)

    def updateTable(self, data, reforme, mode, dataDefault):
        xaxis = CONF.get('simulation', 'xaxis')
        if dataDefault is None:
            dataDefault = data
        headers = dataDefault[xaxis]
        print xaxis
        print dataDefault
        n = len(headers.vals)
        self.data = data
        self.outputModel = OutputModel(data, headers, n , self)
        self.treeView.setModel(self.outputModel)
        self.treeView.expandAll()
        self.treeView.setColumnWidth(0, 200)
        if mode == 'bareme':
            for i in range(n):
                self.treeView.resizeColumnToContents(i+1)
        else:
            self.treeView.setColumnWidth(1,100)

    def saveCsv(self):
        output_dir = CONF.get('paths', 'output_dir')
        user_path = os.path.join(output_dir, 'sans-titre.csv')

        fname = QFileDialog.getSaveFileName(self,
                                               u"Exporter la table", user_path, u"CSV (séparateur: point virgule) (*.csv)")
        
        if fname:
            CONF.set('paths', 'output_dir', os.path.dirname(str(fname)))
            try:
                now = datetime.now()
                csvfile = open(fname, 'wb')
                writer = UnicodeWriter(csvfile, dialect= csv.excel, delimiter=';')
                writer.writerow([u'OpenFisca'])
                writer.writerow([u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M'))])
                writer.writerow([u'Système socio-fiscal au %s' % CONF.get('simulation', 'datesim')])
                writer.writerow([])
                
                for row in self.data:
                    if not row.desc in ('root'):
                        outlist = [row.desc]
                        for val in row.vals:
                            outlist.append(locale.str(val))
                        writer.writerow(outlist)
                csvfile.close()                
            except Exception, e:
                QMessageBox.critical(
                    self, "Error saving file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)

class OutputModel(QAbstractItemModel):
    def __init__(self, root, headers, ncol, parent=None):
        super(OutputModel, self).__init__(parent)
        self._rootNode = root
        self._ncolumn = ncol
        self._headers = headers

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = self.getNode(parent)
        return parentNode.childCount()

    def columnCount(self, parent):
        return self._ncolumn +1
    
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0: 
                return QVariant(node.desc)
            else:
                return QVariant(int(np.round(node.vals[col-1])))
        if role == Qt.TextAlignmentRole:
            if col == 0: 
                return Qt.AlignLeft
            return Qt.AlignRight

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if   section == 0: return QVariant(self._headers.desc)
            else:
                return QVariant(int(self._headers.vals[section-1]))
    
    def flags(self, index):
        node = self.getNode(index)
        if np.any(node.vals != 0):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
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


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

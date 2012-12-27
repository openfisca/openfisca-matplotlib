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

from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant
from PyQt4.QtGui import  QFileDialog, QMessageBox, QWidget, QAbstractItemView
from datetime import datetime
from src.core.qthelpers import OfTreeView
import csv
import os
import codecs
import cStringIO
import locale
import numpy as np
from pandas import DataFrame, ExcelWriter

from src.qt.QtGui import  QVBoxLayout
from src.core.config import get_icon
from src.plugins.__init__ import OpenfiscaPluginWidget

from src.core.utils_old import of_import
from src.core.baseconfig import get_translation
locale.setlocale(locale.LC_ALL, '')
_ = get_translation('src')


class ScenarioTableWidget(OpenfiscaPluginWidget):    
    """
    Scenario Table Widget
    """
    CONF_SECTION = 'composition'

    def __init__(self, parent = None):
        super(ScenarioTableWidget, self).__init__(parent)
        self.setObjectName(_("Table"))
        self.setWindowTitle(_("Table"))
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
        self.setLayout(self.verticalLayout)

        self.table_format = self.get_option('table/format')
        self.output_dir = self.get_option('table/export_dir')


    #------ Public API ---------------------------------------------
    def clearModel(self):
        self.treeView.setModel(None)

    def updateTable(self, simulation):
        '''
        Updates table
        '''
        data = simulation.data
        dataDefault = simulation.data_default
        
        if dataDefault is None:
            dataDefault = data

        mode = simulation.mode
        xaxis = simulation.xaxis
        build_axes = of_import('utils','build_axes', simulation.country)
        axes = build_axes(simulation.country)
        for axe in axes:
            if axe.name == xaxis:
                xaxis_typ_tot = axe.typ_tot_default
                break
            
        headers = dataDefault[xaxis_typ_tot]
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


    def create_dataframe(self):
        '''
        Formats data into a dataframe
        '''
        data_dict = dict()
        index = [] 
        for row in self.data:
            if not row.desc in ('root'):
                index.append(row.desc)
                data_dict[row.desc] = row.vals
                
        df = DataFrame(data_dict).T
        df = df.reindex(index)
        return df

    def create_description(self):
        '''
        Creates a description dataframe
        '''
        now = datetime.now()
        descr =  [u'OpenFisca', 
                         u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M')),
                         u'Système socio-fiscal au %s' % str(self.simulation.datesim)]
        return DataFrame(descr)

    
    def save_table(self):
        
        table_format = self.table_format
        output_dir = self.output_dir
        filename = 'sans-titre.' + table_format
        user_path = os.path.join(output_dir, filename)

        extension = table_format.upper() + "   (*." + table_format + ")"
        fname = QFileDialog.getSaveFileName(self,
                                               _("Save table"), user_path, extension)
        
        if fname:
            self.output_dir = os.path.dirname(str(fname))
            self.set_option('table/export_dir', self.output_dir)
            try:
                if table_format == "xls":
                    writer = ExcelWriter(str(fname))
                    df = self.create_dataframe()
                    descr = self.create_description()
                    df.to_excel(writer, "table", index=True, header= False)
                    descr.to_excel(writer, "description", index = False, header=False)
                    writer.save()
                elif table_format =="csv":
                    # TODO: use DataFrame's ? 
                    now = datetime.now()
                    csvfile = open(fname, 'wb')
                    writer = UnicodeWriter(csvfile, dialect= csv.excel, delimiter=';')
                    
                    for row in self.data:
                        if not row.desc in ('root'):
                            outlist = [row.desc]
                            for val in row.vals:
                                outlist.append(locale.str(val))
                            writer.writerow(outlist)
                            
                    writer.writerow(['OpenFisca'])
                    writer.writerow([_('Computed on %s at %s') % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M'))])
                    writer.writerow([_('Socio-fiscal legislation of date %s') % str(self.simulation.datesim)])
                    writer.writerow([])
            
                    csvfile.close()                
                
            except Exception, e:
                QMessageBox.critical(
                    self, "Error saving file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)


    #------ OpenfiscaPluginMixin API ---------------------------------------------
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return "Table"

    
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
        # set the table model to None before changing data
        if self.main.scenario_simulation.data is not None:
            self.clearModel()
            self.updateTable(self.main.scenario_simulation)
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True



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

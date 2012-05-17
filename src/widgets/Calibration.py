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

from __future__ import division

import os
import numpy as np

from pandas import read_csv, DataFrame

from PyQt4.QtCore import SIGNAL, Qt, QAbstractTableModel, QModelIndex, QVariant, QString, QSize 
from PyQt4.QtGui import (QWidget, QLabel, QDockWidget, QHBoxLayout, QVBoxLayout, 
                         QPushButton, QComboBox, QDoubleSpinBox, QCheckBox, QTableView, 
                         QInputDialog, QFileDialog, QMessageBox, QApplication, QIcon, QPixmap, QCursor)

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


from widgets.matplotlibwidget import MatplotlibWidget

from Config import CONF
from core.columns import BoolCol, AgesCol, EnumCol

class CalibrationWidget(QDockWidget):
    def __init__(self, parent = None):
        super(CalibrationWidget, self).__init__(parent)

        # Create geometry
        self.setWindowTitle("Calibration")
        self.setObjectName("Calibration")
        self.dockWidgetContents = QWidget()        
        verticalLayout = QVBoxLayout(self.dockWidgetContents)

        self.param = {}
                
        # calibration widget

        up_spinbox = MyDoubleSpinBox(self, 'Ratio maximal','','',min_=1, max_=100, step=1, value = CONF.get('calibration', 'up'), changed = self.set_param)
        invlo_spinbox = MyDoubleSpinBox(self, 'Inverse du ratio minimal','','',min_=1, max_=100, step=1, value = CONF.get('calibration', 'invlo'), changed = self.set_param) 
                
        method_choices = [(u'Linéaire', 'linear'),(u'Raking ratio', 'raking ratio'), (u'Logit', 'logit')]
        method_combo = MyComboBox(self, u'Choix de la méthode', method_choices)
        self.connect(method_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_param)
        
        self.param_widgets = {'up': up_spinbox.spin, 'invlo': invlo_spinbox.spin, 'method': method_combo.box}        
                
        calib_lyt = QHBoxLayout()
        calib_lyt.addWidget(up_spinbox)
        calib_lyt.addWidget(invlo_spinbox)
        calib_lyt.addWidget(method_combo)
        verticalLayout.addLayout(calib_lyt)


        self.totalpop = None
        self.aggregate_calculated = False

        # Total population widget
        
        self.pop_checkbox = QCheckBox(u"Ajuster la population totale", self.dockWidgetContents)
        self.pop_spinbox = MyDoubleSpinBox(self.dockWidgetContents, u"Popualtion cible :", u"ménages", option = None ,min_=15e6, max_=30e6, step=5e6, changed = self.set_totalpop)
        self.pop_spinbox.setDisabled(True)
        
        self.totalpop_lyt = QHBoxLayout()
        
        self.totalpop_lyt.addWidget(self.pop_checkbox)
        self.totalpop_lyt.addWidget(self.pop_spinbox)
      
        verticalLayout.addLayout(self.totalpop_lyt)

        # margins 

        self.margins = MarginsTable()        
        self.margins_model = MarginsModel(self.margins, self.dockWidgetContents)
        self.margins_view = QTableView(self.dockWidgetContents)
        self.margins_view.setModel(self.margins_model)
        
        self.init_totalpop()
        
        #   buttons to add and rmv margins
        self.add_input_margin_btn  = QPushButton(u'Ajouter une variable \n (marge renseignée)', self.dockWidgetContents)
        self.add_free_margin_btn = QPushButton('Ajouter une variable \n (marge libre)', self.dockWidgetContents)
        self.add_output_margin_btn = QPushButton(u'Ajouter une variable calculée \n (marge renseignée)', self.dockWidgetContents)
        self.rmv_margin_btn  = QPushButton('Retirer une variable', self.dockWidgetContents)
        self.reset_margin_btn  = QPushButton(u'Réinitialiser', self.dockWidgetContents)
        
        self.save_btn = QPushButton(self.dockWidgetContents)
        self.save_btn.setToolTip(QApplication.translate("Calage", "Sauvegarder les paramètres et cales actuels", None, QApplication.UnicodeUTF8))
        self.save_btn.setText(_fromUtf8(""))
        icon = QIcon()
        icon.addPixmap(QPixmap(_fromUtf8(":/images/document-save.png")), QIcon.Normal, QIcon.Off)
        self.save_btn.setIcon(icon)
        self.save_btn.setIconSize(QSize(22, 22))
        
        self.open_btn = QPushButton(self.dockWidgetContents)
        self.open_btn.setToolTip(QApplication.translate("Parametres", "Ouvrir des paramètres", None, QApplication.UnicodeUTF8))
        self.open_btn.setText(_fromUtf8(""))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(_fromUtf8(":/images/document-open.png")), QIcon.Normal, QIcon.Off)
        self.open_btn.setIcon(icon1)
        self.open_btn.setIconSize(QSize(22, 22))
        self.open_btn.setObjectName(_fromUtf8("open_btn"))

        
        margin_btn_lyt  = QVBoxLayout()
        margin_btn_lyt.addWidget(self.add_input_margin_btn)
        margin_btn_lyt.addWidget(self.add_free_margin_btn)    
        margin_btn_lyt.addWidget(self.add_output_margin_btn)
        margin_btn_lyt.addWidget(self.rmv_margin_btn)
        reset_lyt = QHBoxLayout()
        reset_lyt.addWidget(self.reset_margin_btn)
        reset_lyt.addWidget(self.save_btn)
        reset_lyt.addWidget(self.open_btn)
        margin_btn_lyt.addLayout(reset_lyt)

        # Widgets in layout        
        margins_lyt = QHBoxLayout()
        margins_lyt.addWidget(self.margins_view)
        margins_lyt.addLayout(margin_btn_lyt)

        verticalLayout.addLayout(margins_lyt)

        self.add_output_margin_btn.setDisabled(True)

        # weights ratio plot        
        self.mplwidget = MatplotlibWidget(self.dockWidgetContents)
        verticalLayout.addWidget(self.mplwidget)
        
        self.setWidget(self.dockWidgetContents)            

        # Connect signals
        self.connect(self.pop_checkbox, SIGNAL('clicked()'), self.set_totalpop)
        self.connect(self.add_input_margin_btn, SIGNAL('clicked()'), self.add_input_margin)
        self.connect(self.add_free_margin_btn, SIGNAL('clicked()'), self.add_margin)
        self.connect(self.add_output_margin_btn, SIGNAL('clicked()'), self.add_output_margin)
        self.connect(self.rmv_margin_btn, SIGNAL('clicked()'), self.rmv_margin)
        self.connect(self.reset_margin_btn, SIGNAL('clicked()'), self.reset)
        self.connect(self.save_btn, SIGNAL('clicked()'), self.save_config)
        self.connect(self.open_btn, SIGNAL('clicked()'), self.load_config)

        self.connect(self.parent(), SIGNAL('aggregate_calculated()'), self.update_aggregates)

    def set_totalpop(self):
        if self.pop_checkbox.isChecked():
            self.pop_spinbox.setEnabled(True)
            self.pop_spinbox.spin.setEnabled(True)
            if self.pop_spinbox.spin.isEnabled():
                self.totalpop = self.pop_spinbox.spin.value()
        else:
            self.pop_spinbox.setDisabled(True)
            self.pop_spinbox.spin.setDisabled(True)
            self.totalpop = None    
        self.param_or_margins_changed()

    def init_totalpop(self):
        if self.margins_model._margins._totalpop:
            self.pop_checkbox.setChecked(True)
            self.pop_spinbox.setEnabled(True)
            self.pop_spinbox.spin.setEnabled(True)
            self.pop_spinbox.spin.setValue(self.margins_model._margins._totalpop)
        else:
            self.pop_checkbox.setChecked(False)
            self.pop_spinbox.setDisabled(True)
            self.pop_spinbox.spin.setDisabled(True)
        
    def update_aggregates(self):
        self.set_output_margins_from_file()
        self.add_output_margin_btn.setEnabled(True)
        self.aggregate_calculated = True
        
    def calibrated(self):
#        if not self.margins_model._margins.get_calib_vars():
#            self.reset_margin_btn.setEnabled(True)
        self.emit(SIGNAL('calibrated()')) 
        
    def param_or_margins_changed(self):
        self.update_add_btns()
        self.emit(SIGNAL('param_or_margins_changed()'))
        
    def update_add_btns(self):
        '''
        Update the states of add and remove buttons depending on lists contents
        '''
        if self.margins.input_vars_list:
            self.add_input_margin_btn.setEnabled(True)
        else:
            self.add_input_margin_btn.setDisabled(True)
        if self.margins.free_vars_list:
            self.add_free_margin_btn.setEnabled(True) 
        else:
            self.add_free_margin_btn.setDisabled(True)
        if self.margins.output_vars_list:
            self.add_output_margin_btn.setEnabled(True)
        else:
            self.add_output_margin_btn.setDisabled(True)
        if self.margins._vars_dict:
            self.reset_margin_btn.setEnabled(True)
            self.rmv_margin_btn.setEnabled(True)
        else:
            self.reset_margin_btn.setDisabled(True)
            self.rmv_margin_btn.setDisabled(True)        
        
    def set_inputs_margins_from_file(self, filename = None, year = None):
        if year is None:
            year     = str(CONF.get('calibration','date').year)
        if filename is None:
            fname    = CONF.get('calibration','inputs_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        
        self.margins.set_margins_from_file(filename, year, source="input")
        self.margins_model.update_margins()
        self.init_totalpop()
        self.add_input_margin_btn.setDisabled(True)
        
    def set_output_margins_from_file(self, filename = None, year = None):
        if year is None:
            year     = str(CONF.get('calibration','date').year)
        if filename is None:
            fname    = CONF.get('calibration','pfam_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        self.margins.set_margins_from_file(filename, year, source='output')
        self.margins_model.update_margins()
        self.add_output_margin_btn.setDisabled(True)    
        
    def add_margin(self, from_input = False, from_output = False):
        self.margins_model.add_margin(from_input, from_output)
        self.param_or_margins_changed()
    
    def add_output_margin(self):
        QMessageBox.critical(
                    self, "Erreur", u"Pas encore implémenté",
                    QMessageBox.Ok, QMessageBox.NoButton)
        # TODO: uncomment this wehn implemented self.add_margin(from_output=True)
        self.emit(SIGNAL('calibrated()'))
    
    def add_input_margin(self):
        self.add_margin(from_input=True)
        
    def rmv_margin(self, all_vars = False):
        self.margins_model.rmv_margin(all_vars = all_vars)
        self.param_or_margins_changed()
                                
    def init_param(self):
        '''
        Set initial values of parameters from configuration settings 
        '''
        for parameter in self.param_widgets:
            widget = self.param_widgets[parameter]
            if isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    if unicode(widget.itemData(index).toString()
                               ) == unicode(CONF.get('calibration', 'method')):
                        break
                widget.setCurrentIndex(index)
                
    def set_param(self):
        '''
        Set parameters from box widget values
        '''
        for parameter, widget in self.param_widgets.iteritems():
            if isinstance(widget, QComboBox):
                data = widget.itemData(widget.currentIndex())                
                self.param[parameter] = unicode(data.toString())
            if isinstance(widget, QDoubleSpinBox):
                self.param[parameter] = widget.value()
        self.param_or_margins_changed()        
        return True

    def set_inputs(self, inputs):
        inputs.gen_index(['men', 'fam', 'foy']) # TODO: REMOVE ?
        self.margins._inputs = inputs
        self.inputs = inputs
        ini_totalpop = sum(inputs.get_value("wprm_init", inputs.index['men']))
        totalpop_label = u"Population initiale totale :" + str(ini_totalpop) + u" ménages"
        self.ini_totalpop_label = QLabel(totalpop_label, parent = self.dockWidgetContents) 
        self.totalpop_lyt.addWidget(self.ini_totalpop_label)
        
    def reset(self):
        self.rmv_margin( all_vars=True )
        inputs = self.inputs
        inputs.set_value('wprm', inputs.get_value('wprm_init'),inputs.index['ind'])
        self.pop_checkbox.setChecked(False)        
        self.pop_spinbox.setDisabled(True)
        self.pop_spinbox.spin.setDisabled(True)
        self.set_totalpop()
        self.plotWeightsRatios()
        self.update_add_btns()
                
#    def update_output_margins(self):
#        datatable = self.outputs
#        inputs    = self.inputs
#        w = inputs.get_value("wprm", inputs.index['men']) # TODO wprm_init ?
#        for varname in datatable.description.col_names:
#            varcol = datatable.description.get_col(varname)
#            value = datatable.get_value(varname, inputs.index['men'])            
#            
#            if isinstance(varcol , BoolPresta):
#                self.margins._output_vars[varname] = {}
#                self.margins._output_vars[varname][True]  = sum(w*(value == True))
#                self.margins._output_vars[varname][False] = sum(w*(value == False))
#            else:
#                self.margins._output_vars[varname] = sum(w*(value))
    
    def get_param(self):
        p = {}
        p['method'] = self.param['method']
        p['lo']     = 1/self.param['invlo']
        p['up']     = self.param['up']
        p['use_proportions'] = True
        p['pondini']  = 'wprm_init'
        return p
              
    def calibrate(self):
        margins_dict = self.margins_model._margins.get_calib_vars()
        param = self.get_param()
        print 'param:', param
        print self.totalpop
        
        if self.totalpop is not None:
            margins_dict['totalpop'] = self.totalpop
        try:
            print 'calibration'
            print margins_dict
            print param
            
            self.margins_model._margins._adjusted_margins = self.inputs.update_weights(margins_dict,param=param, return_margins = True)
        except Exception, e:
            raise Exception(u"Vérifier les paramètres:\n%s"% e)
        finally:
            if 'totalpop' in margins_dict:
                del margins_dict['totalpop']
            self.margins_model.update_margins()            

        self.plotWeightsRatios()
        self.calibrated()
                    
    def plotWeightsRatios(self):
        ax = self.mplwidget.axes
        ax.clear()
        weight_ratio = self.inputs.get_value('wprm')/self.inputs.get_value('wprm_init')
        ax.hist(weight_ratio, 50, normed=1, histtype='stepfilled')
        ax.set_xlabel(u"Poids relatifs")
        ax.set_ylabel(u"Densité")
        self.mplwidget.draw()
        
    def save_config(self):
        '''
        Save calibration parameters
        '''
        # TODO: add  param
        # param_dict = self.get_param()
        
        year     = str(CONF.get('calibration','date').year)
        margins_dict = self.margins.get_calib_vars()
        if not margins_dict:
            QMessageBox.critical(
                    self, "Erreur", u"Les marges sont vides" ,
                    QMessageBox.Ok, QMessageBox.NoButton)
            return
            
        data = []
        for varname, value in margins_dict.iteritems():
            if isinstance(value, dict):
                for mod in value.iterkeys():
                    varname = varname 
                    modality = mod
                    margin = margins_dict[varname][mod]
                    data.append({ 'var': varname, 'mod': modality, year: margin}) 
            else:
                modality = 0
                margin = margins_dict[varname]
                data.append({ 'var': varname, 'mod': modality, year: margin})
        
        if self.totalpop:
            data.append({ 'var': 'totalpop', 'mod': 0, year: self.totalpop})
        
        saved = DataFrame(data = data, columns = ['var', 'mod', year])
        # TODO: sort these dataframes ! 
        calib_dir = CONF.get('paths','calib_dir')
        default_fileName = os.path.join(calib_dir, 'sans-titre')
        fileName = QFileDialog.getSaveFileName(self,
                                               u"Enregistrer un calage", default_fileName, u"Calage OpenFisca (*.csv)")
        if fileName:
            try:
                saved.to_csv(fileName, index=False)
            except Exception, e:
                QMessageBox.critical(
                    self, "Erreur", u"Impossible d'enregistrer le fichier : " + str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)
        
    def load_config(self):
        
        year     = str(CONF.get('calibration','date').year)
        calib_dir = CONF.get('paths','calib_dir')
        fileName = QFileDialog.getOpenFileName(self,
                                               u"Ouvrir un calage", calib_dir, u"Calages OpenFisca (*.csv)")
        if not fileName == '':
            try: 
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                self.reset()
                self.margins.set_margins_from_file(fileName, year = year, source='config')
                self.margins_model.update_margins()
                self.init_totalpop()
                
            except Exception, e:
                QMessageBox.critical(
                    self, "Erreur", u"Impossible de lire le fichier : " + str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)
            finally:
                QApplication.restoreOverrideCursor()    
            self.param_or_margins_changed()

class MarginsModel(QAbstractTableModel):
    def __init__(self, margins, parent = None):
        super(MarginsModel, self).__init__(parent)
        self._parent = parent
        self._margins = margins        # MarginsTable object 
        self._adjusted_margins = {}    # Adjusted margins to take into account total population rescaling
    
    def parent(self):
        return self._parent
    
    def rowCount(self, parent = QModelIndex()):
        return self._margins.rowCount()
    
    def columnCount(self, parent =QModelIndex()):
        return self._margins.columnCount()
    
    def flags(self, index):
        col = index.column()
        if col == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0 : return  "Code"
                elif section == 1: return "Cible"
                elif section == 2: return u"Cible ajustée"
                elif section == 3: return u"Marge calibrée"
                elif section == 4: return "Marge initiale"
                elif section == 5: return "Variable"
                elif section == 6: return u"Modalité"        
        
        return super(MarginsModel, self).headerData(section, orientation, role)
    
    def data(self, index, role =  Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return QVariant(self._margins.data(row, col))
        
        if role == Qt.TextAlignmentRole:
            if col != 0: return Qt.AlignRight
        
        return QVariant()

    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        if role == Qt.EditRole:
            if col == 1: self._margins.setData(row, col, value.toPyObject())
            self.dataChanged.emit(index, index)
            return True
        return False
    
    def add_margin(self, from_input = False, from_output = False):
        '''
        Add a margin
        '''
        variables_list = list()
        if from_input:
            variables_list = self._margins.input_vars_list 
            datatable = self._margins._inputs   
        elif from_output:
            variables_list = self._margins.output_vars_list
            datatable = self._margins._outputs
        else:
            if self._margins._inputs:
                datatable = self._margins._inputs
                variables_list = self._margins.free_vars_list

        varnames = {} # {varname: varlabel}
        for var in variables_list:
            varcol  = datatable.description.get_col(var)
            if varcol.label:
                varnames[_fromUtf8(varcol.label)] = var
            else:
                varnames[_fromUtf8(var)] = var
        
        varlabel, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                           sorted(varnames.keys()))
        varname = varnames[varlabel]
        insertion = ok and not(varlabel.isEmpty()) and (varname not in self._margins._vars)
        if insertion :
            nbrow = self._margins.howManyFields(str(varname), datatable)
            self._var_to_insert = str(varname)
            if str(varname) in self._margins._input_vars.keys():
                self._margin_to_insert = self._margins._input_vars[str(varname)]
            else:
                self._margin_to_insert = None
            self._margin_to_insert_datatable = datatable 
            self.insertRows(0,nbrow-1)
            del self._var_to_insert, self._margin_to_insert, self._margin_to_insert_datatable
    
    def rmv_margin(self, all_vars=True):
        '''
        Remove margins (all by default)
        '''

        margins_dict = self._margins.get_calib_vars()
     
        varnames = {} # {varname: varlabel}
        for var in margins_dict:
            if var in  self._margins.output_vars_list:
                datatable = self._margins._outputs
            else:
                datatable = self._margins._inputs
            varcol  = datatable.description.get_col(var)
            if varcol.label:
                varnames[_fromUtf8(varcol.label)] = var
            else:
                varnames[_fromUtf8(var)] = var
        
        varnames_to_rmv = []
        if not all_vars:
            varlabel, ok = QInputDialog.getItem(self.parent(), "Retirer une variable", u"Nom de la variable à retirer", 
                                           sorted(varnames.keys()))
            
            varname = varnames[varlabel]
            
            deletion = ok and not(varlabel.isEmpty())
            if deletion:
                varnames_to_rmv = [varname]
        else:
            varnames_to_rmv = [keys for keys in margins_dict]

        for varname in varnames_to_rmv:
            varname = str(varname)
            if varname in self._margins._output_vars.keys():
                datatable = self._margins._outputs
            else:
                datatable = self._margins._inputs
            nbrow = self._margins.howManyFields(varname, datatable)
            self._margin_to_remove = varname
            self.removeRows(0,nbrow-1)
            del self._margin_to_remove

    def update_margins(self):
        self.beginResetModel()
        self._margins._vars = []
        for var, target in self._margins._vars_dict.iteritems():
            if var in self._margins._input_vars:
                self._margins.addVar(var, self._margins._inputs, target)
            else:
                if self._margins._outputs:
                    self._margins.addVar(var, self._margins._outputs, target)    
        self.endResetModel()

    def insertRows(self, row, count, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row + count)
        self._margins.addVar(self._var_to_insert, self._margin_to_insert_datatable, self._margin_to_insert)
        self.endInsertRows()
        return True
    
    def removeRows(self, row, count, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row + count)
        self._margins.rmvVar(str(self._margin_to_remove))
        self.endRemoveRows()
        return True

class MarginsTable(object):
    '''
    TODO: complete
    '''
    def __init__(self):
        super(MarginsTable, self).__init__()
        self._vars_dict = {}    # dict of strings with varnames and margins 
        self._vars = []         # list of strings with varnames_modality
        self._attr = {}
        self._inputs = None     # datatable of input vars
        self._outputs  = None   # datatable of output vars
        self._adjusted_margins   = {}
        self._input_vars  = {}  # dict of input vars: dict(modality: margins) with margins from external file
        self._output_vars = {}  # dict of output vars: dict(modality: margins) with margins from external file
        self._totalpop = None

    @property
    def input_vars_list(self):
        return sorted(list(set(self._input_vars.keys()) - set(self._vars_dict)))
    
    @property
    def free_vars_list(self):
        return sorted(list(set(self._inputs.col_names) - set(self._vars_dict)))
    
    @property
    def output_vars_list(self):
        return sorted(list(set(self._output_vars.keys()) - set(self._vars_dict)))
    
    def set_inputs(self, inputs):
        self._inputs = inputs
        
    def set_inputs_margins_from_file(self, filename = None, year = None):              
        if year is None:
            year     = str(CONF.get('calibration','date').year)
        if filename is None:
            fname    = CONF.get('calibration','inputs_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        self.set_margins_from_file(filename, year, source="input")
        
    def clear_inputs(self):
        for var in self._input_vars.iterkeys():
            self.rmvVar(var)

    
#        try:
#            f_tot = open(filename)
#            totals = read_csv(f_tot,index_col = 0)
#            marges = {}
#            if self._outputs:
#                for var in totals.index:
#                    if var in self._outputs:
#                        marges[var] = 1e6*totals.get_value(var,year)
#                        self._output_vars[var] = marges[var]
#                        self.addVar(var, self._output, marges[var])
#        except Exception, e:
#                print Warning("Unable to read output margins for %s, output margins left empty because:%s" % (year, e))
#        finally:
#            f_tot.close()

    def clear_outputs(self):
        for var in self._output_vars.iterkeys():
            self.rmvVar(var)        

    def set_margins_from_file(self, filename, year, source):
        try:
            f_tot = open(filename)
            totals = read_csv(f_tot,index_col = (0,1))
            marges = {}
            for var, mod in totals.index:
                if not marges.has_key(var):
                    marges[var] = {}
                marges[var][mod] =  totals.get_value((var,mod),year)
                if var == 'totalpop': 
                    if source == "input" or source == "config" :
                        totalpop = marges.pop('totalpop')[0]
                        marges['totalpop'] = totalpop
                        self._totalpop = totalpop
                else:
                    if source == "input":
                        self._input_vars[var] = marges[var]
                        self.addVar(var, self._inputs, marges[var])
                    if source == 'output':
                        self._output_vars[var] = marges[var]    
                        self.addVar(var, self._outputs, marges[var])
                    if source == "config":
                        if var in self._inputs.col_names:
                            self._input_vars[var] = marges[var]
                            self.addVar(var, self._inputs, marges[var])
        except Exception, e:
            print Warning("Unable to read %(source)s margins for %(year)s, margins left empty because %(e)s" % {'source':source, 'year': year, 'e':e})
        finally:
            f_tot.close()


    def get_calib_vars(self):
        return self._vars_dict

    def rowCount(self):
        return len(self._vars)
    
    def columnCount(self):
        return 7
        
    def data(self, row, col):
        var = str(self._vars[row])
        if   col == 0: return  var
        elif col == 1: return self._attr[var][0] 
        elif col == 2: return self._attr[var][1] 
        elif col == 3: return self._attr[var][2] 
        elif col == 4: return self._attr[var][3] 
        elif col == 5: return self._attr[var][4]
        elif col == 6: return self._attr[var][5]
        
    def setData(self, row, col, value):
        var = self._vars[row]
        if col == 1: self._attr[var][0] = value
        #if col == 2: self._attr[var][1] = value
        
        if var in self._vars_dict:
            self.updateVarDict(var, value)
        else:
            varname, modality = var.split('_')
            self.updateVarDict(varname, value, modality)

    def howManyFields(self, varname, datatable):
        varcol = datatable.description.get_col(varname)
        if isinstance(varcol , BoolCol):
            return 2
        elif isinstance(varcol , AgesCol):
            return len(np.unique(datatable.get_value(varname)))
        elif isinstance(varcol , EnumCol):
            if varcol.enum:
                return varcol.enum._count
            else:
                return len(np.unique(datatable.get_value(varname)))
        else:
            return 1        

    def addVar(self, varname, datatable, target=None):
        varcol = datatable.description.get_col(varname)
        if isinstance(varcol , BoolCol):
            if target is not None:
                ok1 = self.addVar2(varname, datatable, True,  target['True'])
                ok0 = self.addVar2(varname, datatable, False, target['False'])
            else:
                ok1 = self.addVar2(varname, datatable, True)
                ok0 = self.addVar2(varname, datatable, False)    
            return ok1 and ok0
        if isinstance(target , dict):
            modalities = target.keys()
            ok = True
            for modality in modalities:
                if target is not None: 
                    ok2 = self.addVar2(varname, datatable, modality, target[modality])
                else:
                    ok2 = self.addVar2(varname, datatable, modality)
                ok = ok and ok2 
            return ok
        if isinstance(varcol, EnumCol): 
            if (varcol.enum is not None):
                ok = True
                for modality, index in varcol.enum.itervars():
                    ok2 = self.addVar2(varname, datatable, modality)
                    ok = ok and ok2 
                return ok
            else:
                ok = True
                for modality in (np.unique(datatable.get_value(varname))):
                    ok2 = self.addVar2(varname, datatable, modality)
                    ok = ok and ok2 
                return ok
        else:
            ok = self.addVar2(varname, datatable, None, target)
            return ok

    def addVar2(self, varname, datatable, modality = None, target=None):
        if modality is not None:
            varname_mod = "%s_%s" % (varname, modality)
        else:
            varname_mod = varname
        if varname_mod in self._vars:
            return False
        # elif varname not in self._inputs.col_names:
        # raise Exception("The variable %s is not present in the inputs table" % varname)
        # return None
        self._vars.append(varname_mod)
        w_init = self._inputs.get_value("wprm_init", self._inputs.index['men'])
        w = self._inputs.get_value("wprm", self._inputs.index['men'])
        varcol = datatable.description.get_col(varname)
        value = datatable.get_value(varname, self._inputs.index['men'])
        label = varcol.label
        mod_name = None
        if modality is not None:     
            if isinstance(varcol, EnumCol) and (varcol.enum is not None):
                total = sum(w*(value == modality))
                total_init = sum(w_init*(value == modality))
            else:    
                total = sum(w*(value == modality))
                total_init = sum(w_init*(value == modality))
            
  
            if varcol.enum:
                mod_name = varcol.enum._vars[modality]
            else:
                mod_name = modality
        else: 
            total = sum(w*value)
            total_init = sum(w_init*value)
        if not target: 
            target = 0
        if varname_mod in self._adjusted_margins.keys(): # TODO
            new_target = self._adjusted_margins[varname_mod]
        else:
            new_target = 0        
        self._attr[varname_mod] = [float(target), float(new_target), float(total) , float(total_init), label, mod_name]
        self.updateVarDict(varname, target, modality)
        return True

    def rmvVar(self, varname):
        if not varname in self._vars_dict:
            return None

        if isinstance(self._vars_dict[varname], dict):
            for modality in self._vars_dict[varname].iterkeys():
                var_to_remove = "%s_%s" % (varname, modality)
                ind = self._vars.index(var_to_remove)
                self._vars.pop(ind)
                del self._attr[var_to_remove]
        else: 
            var_to_remove = varname
            ind = self._vars.index(var_to_remove)
            self._vars.pop(ind)
            del self._attr[var_to_remove]
        del self._vars_dict[varname]
        
    def updateVarDict(self, varname, target, modality=None):
        if modality is not None:
            if varname not in self._vars_dict:
                self._vars_dict[varname] = {modality: target}
            else:
                self._vars_dict[varname][modality] = target
        else:
            self._vars_dict[varname] = target         


### Some useful widgets
            
class MyDoubleSpinBox(QWidget):
    def __init__(self, parent, prefix = None, suffix = None, option = None, min_ = None, max_ = None,
                 step = None, tip = None, value = None, changed =None):
        super(MyDoubleSpinBox, self).__init__(parent)
    
        if prefix:
            plabel = QLabel(prefix)
        else:
            plabel = None
        if suffix:
            slabel = QLabel(suffix)
        else:
            slabel = None
        spinbox = QDoubleSpinBox(parent)
        if min_ is not None:
            spinbox.setMinimum(min_)
        if max_ is not None:
            spinbox.setMaximum(max_)
        if step is not None:
            spinbox.setSingleStep(step)
        if tip is not None:
            spinbox.setToolTip(tip)
        layout = QHBoxLayout()
        for subwidget in (plabel, spinbox, slabel):
            if subwidget is not None:
                layout.addWidget(subwidget)
        if value is not None:
            spinbox.setValue(value)
        
        if changed is not None:
            self.connect(spinbox, SIGNAL('valueChanged(double)'), changed)

        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.spin = spinbox

class MyComboBox(QWidget):
    def __init__(self, parent, text, choices = None, option = None, tip = None):
        super(MyComboBox, self).__init__(parent)
        """choices: couples (name, key)"""
        label = QLabel(text)
        combobox = QComboBox(parent)
        if tip is not None:
            combobox.setToolTip(tip)
        if choices:
            for name, key in choices:
                combobox.addItem(name, QVariant(key))
        layout = QHBoxLayout()
        for subwidget in (label, combobox):
            layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.box = combobox

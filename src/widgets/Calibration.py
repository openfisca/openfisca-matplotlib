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
import warnings
import numpy as np

from pandas import read_csv

from PyQt4.QtCore import SIGNAL, Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt4.QtGui import (QWidget, QLabel, QDockWidget, QHBoxLayout, QVBoxLayout, 
                         QPushButton, QComboBox, QDoubleSpinBox, QTableView, QInputDialog)
from widgets.matplotlibwidget import MatplotlibWidget

from Config import CONF
from core.qthelpers import OfSs


from core.datatable import SystemSf
from core.columns import BoolPresta
from france.data import BoolCol, AgesCol, EnumCol


class CalibrationWidget(QDockWidget):
    def __init__(self, parent = None):
        super(CalibrationWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setWindowTitle("Calibration")
        self.setObjectName("Calibration")
        self.dockWidgetContents = QWidget()        
        verticalLayout = QVBoxLayout(self.dockWidgetContents)

        self.param = {}
                
        # calibration widget

        up_spinbox = MyDoubleSpinBox('Ratio maximal','','',min_=1,max_=100, step=1, parent = self)
        invlo_spinbox = MyDoubleSpinBox('Inverse du ratio minimal','','',min_=1,max_=100, step=1, parent = self) 
        
        self.connect(up_spinbox.spin, SIGNAL('valueChanged(double)'), self.set_param)
        self.connect(invlo_spinbox.spin, SIGNAL('valueChanged(double)'), self.set_param)
        
        method_choices = [(u'Linéaire', 'linear'),(u'Raking ratio', 'raking ratio'), (u'Logit', 'logit')]
        method_combo = MyComboBox(u'Choix de la méthode', method_choices, parent=self)                 
        self.connect(method_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_param)
        
        self.param_widgets = {'up': up_spinbox.spin, 'invlo': invlo_spinbox.spin, 'method': method_combo.box}        
                
        calib_lyt = QHBoxLayout()
        calib_lyt.addWidget(up_spinbox)
        calib_lyt.addWidget(invlo_spinbox)
        calib_lyt.addWidget(method_combo)
        verticalLayout.addLayout(calib_lyt)

        # Total population widget
        
#       pop_checkbox = QCheckbox # TODO
        self.totalpop = None

        self.pop_spinbox = MyDoubleSpinBox(u"Population cible totale :", u"ménages", option = None ,min_=15e6, max_=30e6, step=5e6, parent = self.dockWidgetContents)
        
        self.connect(self.pop_spinbox.spin, SIGNAL('valueChanged(double)'), self.set_totalpop)
        self.totalpop_lyt = QHBoxLayout()
        self.totalpop_lyt.addWidget(self.pop_spinbox)
      
        verticalLayout.addLayout(self.totalpop_lyt)

        # margins 

        self.margins = Margins()
        self.init_totalpop()
                
        self.margins_model = MarginsModel(self.margins, self.dockWidgetContents)
        self.margins_view = QTableView(self.dockWidgetContents)
        self.margins_view.setModel(self.margins_model)
        self.dockWidgetContents.margins_dict = self.margins_model._margins.get_calib_vars()        
        
        #   buttons to add and rmv margins
        self.add_margin_btn  = QPushButton(u'Ajouter une variable (marge renseignée)', self.dockWidgetContents)
        self.add_margin_btn2 = QPushButton('Ajouter une variable (marge libre)', self.dockWidgetContents)
        self.add_margin_btn3 = QPushButton(u'Ajouter une variable calculée', self.dockWidgetContents)
        rmv_margin_btn  = QPushButton('Retirer une variable', self.dockWidgetContents)
        margin_btn_lyt  = QHBoxLayout()
        margin_btn_lyt.addWidget(self.add_margin_btn)
        margin_btn_lyt.addWidget(self.add_margin_btn2)    
        margin_btn_lyt.addWidget(self.add_margin_btn3)
        self.add_margin_btn3.setDisabled(True)
        margin_btn_lyt.addWidget(rmv_margin_btn)
        self.connect(self.add_margin_btn, SIGNAL('clicked()'), self.add_preset_margin)
        self.connect(self.add_margin_btn2, SIGNAL('clicked()'), self.add_margin)
        self.connect(self.add_margin_btn3, SIGNAL('clicked()'), self.add_postset_margin)
        self.connect(rmv_margin_btn, SIGNAL('clicked()'), self.rmv_margin)

        # Widgets in layout
        verticalLayout.addWidget(self.margins_view)
        verticalLayout.addLayout(margin_btn_lyt)

        # weights ratio plot        
        self.mplwidget = MatplotlibWidget(self.dockWidgetContents)
        verticalLayout.addWidget(self.mplwidget)
        
        self.setWidget(self.dockWidgetContents)            

    def set_totalpop(self):
        self.totalpop = self.pop_spinbox.spin.value()

    def init_totalpop(self):
        self.totalpop = self.margins._totalpop 
        if self.totalpop is not None:
            self.pop_spinbox.spin.setValue(self.totalpop)

    def aggregate_calculated(self):
        self.add_margin_btn3.setEnabled(True)
        
    def calibrated(self):
        self.emit(SIGNAL('calibrated()')) 
        
    def param_or_margins_changed(self):
        self.update_add_btns()
        self.emit(SIGNAL('param_or_margins_changed()'))
        
    def update_add_btns(self):    
        if self.margins.preset_vars_list:
            self.add_margin_btn.setEnabled(True)
        if self.margins.free_vars_list:
            self.add_margin_btn2.setEnabled(True) 
        if self.margins.postset_vars_list:
            self.add_margin_btn3.setEnabled(True)
        
    def set_margins_from_file(self, filename = None, year = None):
        self.margins.set_margins_from_file(filename, year)
        self.init_totalpop()
        self.add_margin_btn.setDisabled(True)
        
    def add_margin(self, from_preset = False, from_postset = False):
        self.margins_model.add_margin(from_preset, from_postset)
        self.param_or_margins_changed()
    
    def add_postset_margin(self):
        self.add_margin(from_postset=True)
        self.param_or_margins_changed()
    
    def add_preset_margin(self):
        self.add_margin(from_preset=True)
        self.param_or_margins_changed()
        
    def rmv_margin(self):
        self.margins_model.rmv_margin()
        self.param_or_margins_changed()
                                
    def init_param(self):
        print 'enter init_param'
        method = CONF.get('calibration', 'method')
        up     = CONF.get('calibration', 'up')
        invlo  = CONF.get('calibration', 'invlo')
        self.param['method'] = str(method)
        self.param['up']     = float(up)
        self.param['invlo']  = float(invlo) 
        print self.param
        # TODO PROBLEM HERE ASK CLEMENT
        for parameter, widget in self.param_widgets.iteritems():
            if isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    if unicode(widget.itemData(index).toString()
                               ) == unicode(self.param[parameter]):
                        break
                print parameter, widget.itemData(index).toString()    
                widget.setCurrentIndex(index)
                
            if isinstance(widget, QDoubleSpinBox):
                print self.param
                print parameter, self.param[parameter]
                widget.setValue(float(self.param[parameter]))
        print self.param

    def set_param(self):
        for parameter, widget in self.param_widgets.iteritems():
            if isinstance(widget, QComboBox):
                data = widget.itemData(widget.currentIndex())                
                self.param[parameter] = unicode(data.toString())
            if isinstance(widget, QDoubleSpinBox):
                self.param[parameter] = widget.value()
        return True

    def set_inputs(self, inputs):
        inputs.gen_index(['men', 'fam', 'foy']) # TODO REMOVE ?
        self.margins._inputs = inputs
        self.inputs = inputs
        ini_totalpop = sum(inputs.get_value("wprm_init", inputs.index['men']))
        totalpop_label = u"Population initiale totale :" + str(ini_totalpop) + u" ménages"
        self.ini_totalpop_label = QLabel(totalpop_label, parent = self.dockWidgetContents) 
        self.totalpop_lyt.addWidget(self.ini_totalpop_label)
                    
    def set_system(self, system):
        self.system = system # TODO homogenize notations: model is called population in MainWindow
        self.margins.set_system(system)
    
    def reset_postset_margins(self):
        self.margins._postset_vars = {}
        
    def update_postset_margins(self):
        datatable = self.system
        inputs    = self.inputs
        margins = {}
        w = inputs.get_value("wprm", inputs.index['men']) # TODO wprm_init ?
        for varname in datatable.description.col_names:
            varcol = datatable.description.get_col(varname)
            value = datatable.get_value(varname, inputs.index['men'])            
            
            if isinstance(varcol , BoolPresta):
                margins[varname] = {}
                margins[varname][True]  = sum(w*(value == True))
                margins[varname][False] = sum(w*(value == False))
                
            else:
                margins[varname] = sum(w*(value))
                            
        self.margins._postset_vars = margins    
        
    def calibrate(self):
        self.margins_dict = self.margins_model._margins.get_calib_vars()

        print self.param
        param = self.param.copy()
        param['lo'] = 1/param['invlo']
        del param['invlo']
        param['use_proportions'] = True
        param['pondini']  = 'wprm_init'
        if self.totalpop is not None:
            self.margins_dict['totalpop'] = self.totalpop
        print self.margins_dict.keys()
        self.margins_model._margins._marges_new = self.system.update_weights(self.margins_dict,param=param, return_margins = True)
        if 'totalpop' in self.margins_dict:
            del self.margins_dict['totalpop']
        self.margins_model.update_margins()            

#        weight_ratio = self.inputs.get_value('wprm')/self.inputs.get_value('wprm_init')
#        print 'low ratios: ',  np.sort(weight_ratio)[1:5]
#        print 'large ratios : ' ,  np.sort(weight_ratio)[-5:]
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
        NotImplemented
        
    def load_config(self):
        NotImplemented    

class MarginsModel(QAbstractTableModel):
    def __init__(self, margins, parent = None):
        super(MarginsModel, self).__init__(parent)
        self._parent = parent
        self._margins = margins
        self._marges_new = {}
    
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
                if section == 0 : return  "Variable"
                elif section == 1: return "Cible"
                elif section == 2: return u"Cible ajustée"
                elif section == 3: return u"Marge calibrée"
                elif section == 4: return "Marge initiale"        
        
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
    
    def add_margin(self, from_preset = False, from_postset = False):
        
        variables_list = list()
        if from_preset:
#            variables_list = sorted(list(set(self._margins._preset_vars.keys()) - set(self._margins._vars_dict)))
            variables_list = self._margins._preset_vars_list 
            datatable = self._margins._inputs   
        elif from_postset:
            variables_list = self._margins._postset_vars_list
#            sorted(list( set(self._margins._postset_vars.keys()) - set(self._margins._vars_dict)))           
            datatable = self._margins._system
        else:
            if self._margins._inputs:
                datatable = self._margins._inputs
                variables_list = self.margins._free_vars_list
                # sorted(list( set(self._margins._inputs.col_names) - set(self._margins._vars_dict) ))
        
        # TODO disable button if variable_list is empty
        
        varname, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                           variables_list)
        insertion = ok and not(varname.isEmpty()) and (varname not in self._margins._vars)
        if insertion :
            nbrow = self._margins.howManyFields(str(varname), datatable)
            self._margin_to_insert = str(varname)
            self._margin_to_insert_datatable = datatable 
            self.insertRows(0,nbrow-1)
            del self._margin_to_insert, self._margin_to_insert_datatable
    
    def rmv_margin(self):
        varname, ok = QInputDialog.getItem(self.parent(), "Retirer une variable", u"Nom de la variable à retirer", 
                                           sorted(self.parent().margins_dict))
        deletion = ok and not(varname.isEmpty())
        if deletion:
            # TODO 
            varname = str(varname)
            if varname in self._margins._postset_vars.keys():
                datatable = self._margins._system
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
            if var in self._margins._preset_vars:
                self._margins.addVar(var, self._margins._inputs, target)
            else:
                self._margins.addVar(var, self._margins._system, target)    
        self.endResetModel()

    def insertRows(self, row, count, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row + count)
        self._margins.addVar(self._margin_to_insert, self._margin_to_insert_datatable, None)
        self.endInsertRows()
        return True
    
    def removeRows(self, row, count, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row + count)
        self._margins.rmvVar(str(self._margin_to_remove))
        self.endRemoveRows()
        return True

class Margins(object):
    def __init__(self):
        super(Margins, self).__init__()
        self._vars_dict = {} # list of strings with varnames
        self._vars = []       # list of strings with varnames
        self._attr = {}
        self._inputs = None
        self._system  = None
        self._marges_new   = {}
        self._preset_vars  = {}
        self._postset_vars = {}
        self._totalpop = None

    @property
    def preset_vars_list(self):
        return sorted(list(set(self._preset_vars.keys()) - set(self._vars_dict)))
    
    @property
    def free_vars_list(self):
        return sorted(list(set(self._inputs.col_names) - set(self._vars_dict)))
    
    @property
    def postset_vars_list(self):
        return sorted(list(set(self._postset_vars.keys()) - set(self._vars_dict)))
    
    def set_inputs(self, inputs):
        self._inputs = inputs
        
    def set_system(self, system):
        self._system = system    

    def set_margins_from_file(self, filename = None, year = None):
                
        if year is None:
            year     = str(CONF.get('calibration','date').year)

        if filename is None:
            fname    = CONF.get('calibration','filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        
        f_tot = open(filename)
        totals = read_csv(f_tot,index_col = (0,1))

        try:
            marges = {}
            for var, mod in totals.index:
                if not marges.has_key(var):
                    marges[var] = {}

                marges[var][mod] =  totals.get_value((var,mod),year)
                if var == 'totalpop': 
                    totalpop = marges.pop('totalpop')[0]
                    marges['totalpop'] = totalpop
                    self._totalpop = totalpop
                else:
                    self._preset_vars[var] = marges[var]
                    self.addVar(var, self._inputs, marges[var])
        except Exception, e:
                print e
                warnings.warn("Unable to read preset margins for %s, pressetted margins left empty" % (year))
            
        f_tot.close()

    def get_calib_vars(self):
        return self._vars_dict    

    def rowCount(self):
        return len(self._vars)
    
    def columnCount(self):
        return 5
        
    def data(self, row, col):
        var = str(self._vars[row])
        if   col == 0: return  var
        elif col == 1: return self._attr[var][0] 
        elif col == 2: return self._attr[var][1] 
        elif col == 3: return self._attr[var][2] 
        elif col == 4: return self._attr[var][3] 

        
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
        if modality is not None:     
            if isinstance(varcol, EnumCol) and (varcol.enum is not None):
                total = sum(w*(value == varcol.enum[modality]))
                total_init = sum(w_init*(value == varcol.enum[modality]))
            else:    
                total = sum(w*(value == modality))
                total_init = sum(w_init*(value == modality))
        else: 
            total = sum(w*value)
            total_init = sum(w_init*value)
        if not target: 
            target = 0
        if varname_mod in self._marges_new.keys(): # TODO
            new_target = self._marges_new[varname_mod]
        else:
            new_target = 0        
        self._attr[varname_mod] = [float(target), float(new_target), float(total) , float(total_init)]
        
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
    def __init__(self, prefix = None, suffix = None, option = None, min_ = None, max_ = None,
                 step = None, tip = None, parent = None):
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
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.spin = spinbox

class MyComboBox(QWidget):
    def __init__(self, text, choices = None, option = None, tip = None, parent = None):
        super(MyComboBox, self).__init__(parent)
        """choices: couples (name, key)"""
        label = QLabel(text)
        combobox = QComboBox(parent)
        if tip is not None:
            combobox.setToolTip(tip)
        for name, key in choices:
            combobox.addItem(name, QVariant(key))
        layout = QHBoxLayout()
        for subwidget in (label, combobox):
            layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.box = combobox        
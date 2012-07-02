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

from PyQt4.QtCore import SIGNAL, Qt, QSize 
from PyQt4.QtGui import (QLabel, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, 
                         QSpinBox, QDoubleSpinBox, QCheckBox, QInputDialog, QFileDialog, 
                         QMessageBox, QApplication, QCursor, QSpacerItem, QSizePolicy,
                         QDialogButtonBox)
from Config import CONF
from core.qthelpers import DataFrameViewWidget, get_icon, _fromUtf8



class InflationWidget(QDialog):
    def __init__(self,  inputs, parent = None):
        super(InflationWidget, self).__init__(parent)


        self.targets_df = None

        self.setWindowTitle("Inflation")
        self.setObjectName("Inflation")
        
        # Totals table view
        self.view = DataFrameViewWidget(self)

        add_var_btn  = self.add_toolbar_btn(tooltip = u"Ajouter une variable de calage",
                                        icon = "list-add.png")
        rmv_var_btn = self.add_toolbar_btn(tooltip = u"Retirer une variable de calage",
                                        icon = "list-remove.png")
        rst_var_btn = self.add_toolbar_btn(tooltip = u"Retirer toutes les variables de calage",
                                        icon = "view-refresh.png")
        inflate_btn = self.add_toolbar_btn(tooltip = u"Inflater les variables",
                                             icon = "calculator_red.png")

        # TODO         save_btn, open_btn
        toolbar_btns = [add_var_btn, rmv_var_btn, rst_var_btn, inflate_btn]
        toolbar_lyt = QHBoxLayout()

        for btn in toolbar_btns:
            toolbar_lyt.addWidget(btn)

        # Build layouts
        verticalLayout = QVBoxLayout(self)
        verticalLayout.addLayout(toolbar_lyt)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel| QDialogButtonBox.Ok, parent = self)
        verticalLayout.addWidget(button_box)

        self.connect(add_var_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(rmv_var_btn, SIGNAL('clicked()'), self.rmv_var)
        self.connect(rst_var_btn, SIGNAL('clicked()'), self.rst_var)
        self.connect(inflate_btn, SIGNAL('clicked()'), self.inflate)
        self.connect(button_box, SIGNAL('accepted()'), self.accept);
        self.connect(button_box, SIGNAL('rejected()'), self.reject);


    def add_toolbar_btn(self, tooltip = None, icon = None):
        btn = QPushButton(self)
        if tooltip:
            btn.setToolTip(tooltip)
        if icon:
            icn = get_icon(icon)
            btn.setIcon(icn)
            btn.setIconSize(QSize(22, 22))
        return btn

    def set_inputs(self, inputs):
        self.inputs = inputs
        
    def set_inputs_targets_from_file(self, filename = None, year = None):
        if year is None:
            year     = str(CONF.get('simulation','datesim').year)
        if filename is None:
            fname    = CONF.get('calibration','inflation_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
            
    
    
    
    def add_var(self, target= None):
        '''
        Adds a variable to the targets
        '''
        variables_list = self.targets["var"]
        varnames = self.get_name_label_dict(variables_list) # {varname: varlabel}
        
        varlabel, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                           sorted(varnames.keys()))
        
        insertion = ok and not(varlabel.isEmpty()) and (varlabel in sorted(varnames.keys()))
        if insertion:
            varname = varnames[varlabel]
            #varcol = self.inputs.description.get_col(varname) 
            
            if target:
                self.add_var2(varname, target = target)
                self.inflation_targets_changed() # targets_changed
    
    def add_var2(self, varname, target=None):
        '''
        Add a variable in the dataframe
        '''
        w_init = self.weights_init
        w = self.weights

        varcol = self.get_col(varname)
        idx = self.inputs.index[self.unit]
        enum = self.inputs.description.get_col('qui'+self.unit).enum
        people = [x[1] for x in enum]


        value = self.inputs.get_value(varname, index = idx)
        
        label = varcol.label
        # TODO: rewrite this using pivot table
        items = [ ('marge'    , w  ), ('marge initiale' , w_init )]        
        if varcol.__class__  in MODCOLS:
            items.append(('mod',   value))
            df = DataFrame.from_items(items)
            res = df.groupby('mod', sort= True).sum()
        else:
            res = DataFrame(index = ['total'], 
                            data = {'marge' : (value*w).sum(),
                                    'marge initiale' : (value*w_init).sum()  } )
        res.insert(0, u"modalités",u"")
        res.insert(2, "cible", 0)
        res.insert(2, u"cible ajustée", 0)
        res.insert(4, "source", source)
        mods = res.index
    
        if target is not None:
            if len(mods) != len(target.keys()):
                print 'Problem with variable : ', varname
                print len(target.keys()), ' target keys for ', len(mods), ' modalities' 
                print 'Skipping the variable'
                drop_indices = [ (varname, mod) for mod in target.keys()]
                if source == 'input':                    
                    self.input_margins_df = self.input_margins_df.drop(drop_indices)
                    self.input_margins_df.index.names = ['var','mod']
                if source == 'output':
                    self.output_margins_df = self.output_margins_df.drop(drop_indices)
                    self.output_margins_df.index.names = ['var','mod']
                return

        if isinstance(varcol, EnumCol):
            if varcol.enum:
                enum = varcol.enum
                res[u'modalités'] = [enum._vars[mod] for mod in mods]
                res['mod'] = mods
            else:
                res[u'modalités'] = [mod for mod in mods]
                res['mod'] = mods
        elif isinstance(varcol, BoolCol) or isinstance(varcol, BoolPresta):
            res[u'modalités'] = bool(mods)
            res['mod']        = mods
        elif isinstance(varcol, AgesCol):
            res[u'modalités'] = mods
            res['mod'] = mods
        else:
            res[u'modalités'] = "total"
            res['mod']  = 0

        if label is not None:
            res['variable'] = label
        else:
            res['variable'] = varname
        res['var'] = varname

        if target is not None: 
            for mod, margin in target.iteritems():
                if mod == varname:    # dirty to deal with non catgorical data
                    res['cible'][0] = margin
                else:
                    res['cible'][mod] = margin     
                        
        if self.frame is None:
            self.frame = res
        else: 
            self.frame = concat([self.frame, res])
        
        self.frame = self.frame.reset_index(drop=True)

    
    
    
                
                
    def inflation_targets_changed(self):
        self.update_view()
        self.emit(SIGNAL('inflation_targets_changed()'))
                
    def update_view(self):
        self.view.clear()
        if self.frame is not None:
            df = self.frame.reset_index(drop=True)
            df_view = df[ ["var", "total (poids initiaux)", "total (poids calibrés)", "cible", "variable" ]]            
            self.view.set_dataframe(df_view)
        self.view.reset()
        
        
                

    def get_name_label_dict(self, variables_list):
        '''
        Builds a dict with label as keys and varname as value
        '''
        varnames = {}
        for varname in variables_list:
            varcol = self.inputs.description.get_col(varname)
            if varcol:
                if varcol.label:
                    varnames[_fromUtf8(varcol.label)] = varname
                else:
                    varnames[_fromUtf8(varname)] = varname
            
        return varnames
    
    

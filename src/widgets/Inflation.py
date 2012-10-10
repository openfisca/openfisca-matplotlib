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
from numpy import logical_and, unique
from pandas import read_csv, DataFrame, concat, HDFStore
from Config import CONF
from core.qthelpers import DataFrameViewWidget, get_icon, _fromUtf8



class InflationWidget(QDialog):
    def __init__(self,  inputs, parent = None):
        super(InflationWidget, self).__init__(parent)


        self.targets_df = None
        self.frame = None

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
        
        verticalLayout.addWidget(self.view)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel| QDialogButtonBox.Ok, parent = self)
        verticalLayout.addWidget(button_box)

        self.connect(add_var_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(rmv_var_btn, SIGNAL('clicked()'), self.rmv_var)
        self.connect(rst_var_btn, SIGNAL('clicked()'), self.rst_var)
        self.connect(inflate_btn, SIGNAL('clicked()'), self.inflate)
        self.connect(button_box, SIGNAL('accepted()'), self.accept);
        self.connect(button_box, SIGNAL('rejected()'), self.reject);

        self.set_inputs(inputs)
        self.set_targets_from_file()

        self.actualisation_coeffs = None
        
    
    @property
    def frame_vars_list(self):
        '''
        List of the variables appearing in the frame (and the dataframe)
        '''
        if self.frame:
            df = self.frame
            if 'var' in df.columns: 
                return list(df['var'])
        else:
            return []
    
    @property
    def target_vars_list(self):
        '''
        List of the variables appearing in the targets dataframe
        '''
        if self.targets_df:
            df = self.targets_df 
            return list((df.index))
        else:
            return []
        
    
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
        '''
        Sets inputs datatable
        '''
        self.inputs = inputs
        self.unit = 'ind'
        self.weights = 1*self.inputs.get_value("wprm", inputs.index[self.unit]) # 1* to deal with pointer nature

    def set_targets_from_file(self, filename = None, year = None):
        '''
        Loads targets from file and display them in the frame
        '''
        
        if year is None:
            year     = str(CONF.get('simulation','datesim').year)
        if filename is None:
            fname = 'inflate.csv'
            #fname    = CONF.get('calibration','inflation_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        with open(filename) as f_tot:
            totals = read_csv(f_tot)
        if year in totals:
            if self.targets_df is None:
                self.targets_df = DataFrame(data = {"var" : totals["var"],
                              "cible" : totals[year]  } )
                
                condition = logical_and(self.targets_df["var"].isin(set(self.inputs.description.col_names)), 
                                        (self.targets_df["cible"] > 0)) 
                self.targets_df = self.targets_df[condition]
                self.targets_df = self.targets_df.set_index("var")
                df = self.targets_df
                self.targets_df['total initial'] = 0

            for varname in self.targets_df.index:
                target = df.get_value(varname, "cible")
                self.add_var2(varname, target=target)
            
        self.inflation_targets_changed()

    def inflate(self):
        '''
        Computest inflators for the displayed variables 
        '''
        table = self.inputs.table
        df = self.targets_df
        
        for varname in self.frame_vars_list:
            self.rmv_var(varname)
            target = df.get_value(varname, "cible") 
            if varname in table:
                x = sum(table[varname]*table['wprm'])/target                    
                if x>0:
                    self.add_var2(varname, target=target, inflator = 1.0/x)
            self.inflated()


    def build_actualisation_groups(self):
        '''
        Builds actualisation groups
        '''
        groups = dict()
        data_dir = CONF.get('paths', 'data_dir')
        fname = "actualisation_groups.h5"
        filename = os.path.join(data_dir, fname)
        store = HDFStore(filename)
        df = store['actualisation']
        coeff_list = sorted(unique(df['coeff'].dropna()))
        for coeff in coeff_list:
            groups[coeff] = list(df[ df['coeff']==coeff ]['var'])

        self.actualisation_groups = groups
            
    def actualise_using_group(self):
        '''
        Actualises the parameters
        '''
        table = self.inputs.table

        for coeff, varname in self.actualisation_groups.iteriterms():
            if varname in table:
                total = sum(table[varname]*table['wprm'])
                target = coeff*total                    
                self.add_var2(varname, target=target, inflator = coeff)
        self.inflated()
        
        
    
# demo : coefficient démographique (tous les poids sont augmentés proportionnellement à ce coefficient)
# sal : coefficient d'actualisation des salaires
# ret : coefficient d'actualisation des pensions hors pensions alimentaires
# pen : coefficient d'actualisation des pensions alimentaires
# rto : coefficient d'actualisation des rentes viagères à titre onéreux
# chd : coefficient d'actualisation des charges déductibles
# red : coefficient d'actualisation des réductions et crédits d'impôts
# rcm : coefficient d'actualisation des revenus de capitaux mobiliers
# rcm_ci : coefficient d'actualisation des revenus de capitaux mobiliers (Crédits d'impôts)
# fon : coefficient d'actualisation des revenus fonciers
# fon_df : coefficient d'actualisation des revenus fonciers (déficits)
# agr : coefficient d'actualisation des bénéfices agricoles
# agr_df : coefficient d'actualisation des bénéfices agricoles (déficits)
# bic : coefficient d'actualisation des bénéfices industriels et commerciaux
# bic_df : coefficient d'actualisation des bénéfices industriels et commerciaux (déficits)
# bic_ae : coefficient d'actualisation bénéfices industriels et commerciaux (auto-entrepreneurs)
# bnc : coefficient d'actualisation des bénéfices non-commerciaux 
# bnc_df : coefficient d'actualisation des bénéfices non-commerciaux (déficits)
# bnc_ae : coefficient d'actualisation des bénéfices non-commerciaux (auto-entrepreneurs)
# pv : coefficient d'actualisation des plus-values
# mv : coefficient d'actualisation des moins-values
# pvm : coefficient d'actualisation des plus-values mobilières
        
        
        

    def add_var(self):
        '''
        Adds a variable to the targets
        '''
        # variables_list = sorted(list(set(self.inputs.description.col_names)-set(self.frame_vars_list)))
        variables_list = sorted(list(set(self.target_vars_list)-set(self.frame_vars_list)))
        varnames = self.get_name_label_dict(variables_list) # {varname: varlabel}
        
        if varnames:
            varlabel, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                       sorted(varnames.keys()))
        else:
            QMessageBox.critical(self, "Erreur", u"Toutes les variables sont déja présentes dans la table" ,
                QMessageBox.Ok, QMessageBox.NoButton)
            return
        
        insertion = ok and not(varlabel.isEmpty()) and (varlabel in sorted(varnames.keys()))
        if insertion:
            varname = varnames[varlabel]
            #varcol = self.inputs.description.get_col(varname) 
            df = self.targets_df
            target = df.get_value(varname, "cible")
            self.add_var2(varname, target = target)
            self.inflation_targets_changed() # targets_changed
    
    def add_var2(self, varname, target=None, inflator = None):
        '''
        Add a variable in the displayed frame
        '''
        w = self.weights

        varcol = self.inputs.description.get_col(varname)
        idx = self.inputs.index[self.unit]
        value = self.inputs.get_value(varname, index = idx)
            
        label = varcol.label
        res = DataFrame(index = [varname], data = {'var'   : varname})
        total = (value*w).sum()
        res['total initial'] = total
        
        if inflator is None:
            self.targets_df.set_value(varname, 'total initial', total)
            inflator = 1
        
        res['inflateur'] = 100*inflator
        res[u'total inflaté'] = inflator*total
        
        if label is not None:
            res['variable'] = label
        else:
            res['variable'] = varname

        if target is not None:
            res['cible'] = target     
                        
                        
        if self.frame is None:
            self.frame = res
        else: 
            self.frame = concat([self.frame, res])

        
    def rmv_var(self, varname = None):
        '''
        Removes variable from the frame
        '''
        if varname is None:
            vars_in_table = self.frame_vars_list
            varnames = self.get_name_label_dict(vars_in_table)        
            varlabel, ok = QInputDialog.getItem(self.parent(), "Retirer une variable", "Nom de la variable", 
                                           sorted(varnames.keys()))
            varname = varnames[varlabel]
            deletion = ok and not(varlabel.isEmpty())
        else:
            if varname in self.frame['var']:
                deletion = True
        if deletion:
            df =  self.frame
            cleaned = df[df['var'] != varname]
            self.frame = cleaned 
        self.inflation_targets_changed()
    
    def rst_var(self):
        '''
        Removes all variables from the margins
        '''
        self.frame = None
        self.update_view()
    
    def inflated(self):
        self.update_view()
        self.emit(SIGNAL('inflated()'))
                
    def inflation_targets_changed(self):
        self.update_view()
        self.emit(SIGNAL('inflation_targets_changed()'))
                
    def update_view(self):
        '''
        Update the displayed dataframe view
        '''
        self.view.clear()
        if self.frame is not None:
            df = self.frame.reset_index(drop=True)
            df_view = df[ ["var", "cible", "total initial", u"total inflaté", "inflateur", "variable"]]
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
    
    
    def accept(self):
        '''
        Updates inputs variables and close dialog
        '''
        for varname in self.frame_vars_list:
            table = self.inputs.table
            target = self.frame.get_value(varname, "cible") 
            if varname in table:
                x = sum(table[varname]*table['wprm'])/target                   
                if x>0:
                    table[varname] = table[varname]/x

        self.parent().emit(SIGNAL('inflated()'))

        QDialog.accept(self)

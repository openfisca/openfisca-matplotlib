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
from numpy import logical_and, unique, NaN
from pandas import  DataFrame, concat, HDFStore
from Config import CONF
from core.qthelpers import DataFrameViewWidget, get_icon, _fromUtf8



class InflationWidget(QDialog):
    def __init__(self,  inputs = None, parent = None):
        super(InflationWidget, self).__init__(parent)

        self.vars_df = None
        self.frame = None

        self.setWindowTitle("Inflator")
        self.setObjectName("Inflator")
        
        # Totals table view
        self.view = DataFrameViewWidget(self)
        self.coeff_view = DataFrameViewWidget(self)


#        add_var_btn  = self.add_toolbar_btn(tooltip = u"Ajouter une variable de calage",
#                                        icon = "list-add.png")
#        rmv_var_btn = self.add_toolbar_btn(tooltip = u"Retirer une variable de calage",
#                                        icon = "list-remove.png")
        
        self.set_inputs(inputs)
        self.survey_year =  inputs.survey_year
        self.datesim_year  = CONF.get('simulation','datesim').year

        print " Inflate survey values for year " + str(self.survey_year) + " to year " + str(self.datesim_year)
        label = QLabel(" Inflate survey values taken for year " + str(self.survey_year) + " to year " + str(self.datesim_year))
        rst_var_btn = self.add_toolbar_btn(tooltip = u"Retirer toutes les variables de calage",
                                        icon = "view-refresh.png")
        inflate_btn = self.add_toolbar_btn(tooltip = u"Inflater les variables",
                                             icon = "calculator_red.png")

        # TODO         save_btn, open_btn
#        toolbar_btns = [add_var_btn, rmv_var_btn, rst_var_btn, inflate_btn]
        toolbar_btns = [rst_var_btn, inflate_btn]
        toolbar_lyt = QHBoxLayout()

        for btn in toolbar_btns:
            toolbar_lyt.addWidget(btn)

        # Build layouts
        verticalLayout = QVBoxLayout(self)
        
        verticalLayout.addLayout(toolbar_lyt)
        verticalLayout.addWidget(label)
        verticalLayout.addWidget(self.coeff_view)
        verticalLayout.addWidget(self.view)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel| QDialogButtonBox.Ok, parent = self)
        verticalLayout.addWidget(button_box)

#        self.connect(add_var_btn, SIGNAL('clicked()'), self.add_var)
#        self.connect(rmv_var_btn, SIGNAL('clicked()'), self.rmv_var)
        self.connect(rst_var_btn, SIGNAL('clicked()'), self.rst_var)
        self.connect(inflate_btn, SIGNAL('clicked()'), self.inflate)
        self.connect(button_box, SIGNAL('accepted()'), self.accept);
        self.connect(button_box, SIGNAL('rejected()'), self.reject);

        if inputs is not None:
            self.set_targets_from_file()

        
    
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
        if self.vars_df:
            df = self.vars_df 
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
            fname = "actualisation_groups.h5"
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)    
            
        store = HDFStore(filename)
            
        # Builds openfisca variables from irpp declaration variables
        df_c = store["corresp"]
        of_vars = dict()
        for col in df_c.columns:
            of_vars[col] = list(unique(df_c[col]).dropna())
            
        df_a = store['amounts']
        df_b = store['benef']
        store.close()

        df_a1 = DataFrame( {'amount' : df_a[year]})
        
        df_a = DataFrame( columns = ['amount'] )
        
        for of_var, declar_vars_list in of_vars.iteritems():
            amount = 0
            for case in declar_vars_list:
                a = df_a1.get_value(case, 'amount')
                if a is not NaN:
                    amount += a 
            df_a1 = df_a1.drop(declar_vars_list, axis = 0)
            row = DataFrame(dict(amount = [amount]), index = [of_var] )
            df_a = df_a.append(row)

        df_a = df_a.append(df_a1)

        self.vars_df = df_a
        self.vars_df.index.names = ['var']
        self.fill_vars()
        self.fill_coeffs()

    def fill_vars(self):
        '''
        Fill the variables dataframe
        '''
        label2var, var2label, var2enum = self.inputs.description.builds_dicts()


        self.vars_df['variable'] = ""
        self.vars_df['total initial'] = NaN
             
        for varname in self.vars_df.index:
            if varname not in self.inputs.description.col_names: 
                self.vars_df = self.vars_df.drop(varname)
                continue
            
            w = self.weights
            idx = self.inputs.index[self.unit]
            value = self.inputs.get_value(varname, index = idx)
                
            label = var2label[varname]
            self.vars_df.set_value(varname, 'variable', label)
            self.vars_df.set_value(varname, 'total initial', (value*w).sum())
            self.vars_df.set_value(varname, u'total inflaté', self.vars_df.get_value(varname, 'total initial'))
        
        
        self.inflation_targets_changed()


    def fill_coeffs(self):
        self.build_actualisation_groups()
        
        list_coeffs = list(self.coeffs_df.index)
        list_coeffs.remove(u"demo")
        demo = self.coeffs_df.get_value(u"demo", "value")
        
        
        for coeff in list_coeffs:
            if coeff not in self.actualisation_vars:
                print coeff + ' not in actualisation vars, continuing'
                continue
            for varname in self.actualisation_vars[coeff]:
                if varname not in self.inputs.description.col_names:
                    continue
                inflator = demo*self.coeffs_df.get_value(coeff, "value")
                self.vars_df.set_value(varname, u'total inflaté', inflator*self.vars_df.get_value(varname, 'total initial'))
                
        self.update_view()
            

    def inflate(self):
        '''
        Computest inflators for the displayed variables 
        '''
        table = self.inputs.table
        df = self.vars_df
        
        for varname in self.frame_vars_list:
            self.rmv_var(varname)
            target = df.get_value(varname, "cible") 
            if varname in table:
                x = sum(table[varname]*table['wprm'])/target                    
                if x>0:
                    self.add_var2(varname, target=target, inflator = 1.0/x)
            self.inflated()


    def build_actualisation_groups(self, filename = None):
        '''
        Builds actualisation groups
        '''
        if filename is None:
            data_dir = CONF.get('paths', 'data_dir')
            fname = "actualisation_groups.h5"
            filename = os.path.join(data_dir, fname)
        
        store = HDFStore(filename)
        df = store['vars']
        coeff_list = sorted(unique(df['coeff'].dropna()))
        
        vars = dict()
        for coeff in coeff_list:
            vars[coeff] = list(df[ df['coeff']==coeff ]['var'])

        self.actualisation_vars = vars
        self.coeffs_df = store['names']
        self.coeffs_df['coeff'] = self.coeffs_df['coeff'].str.replace(' ','') # remove spaces
        

        
        yr = 1*self.survey_year
        self.coeffs_df['value'] = 1
        while yr < self.datesim_year:
            if yr in self.coeffs_df.columns:
                factor = self.coeffs_df[yr]
            else:
                factor =    1 
            self.coeffs_df['value'] = self.coeffs_df['value']*factor
            yr += 1
        
        self.coeffs_df.set_index(['coeff'], inplace = True)
        store.close()   
           

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
            df = self.vars_df
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
            self.vars_df.set_value(varname, 'total initial', total)
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
        if self.vars_df is not None:
            df = self.vars_df.reset_index(drop=False)
            df.rename(columns = {'amount' : u'sources administratives'}, inplace= True)
            print df.to_string()
            #df.rename  = ['var']
#            df_view = df[ ["var", "cible", "total initial", u"total inflaté", "inflateur", "variable"]]
            df_view = df
            #df[ ["index", "amount", "total initial", u"total inflaté", "variable"]]

            self.view.set_dataframe(df_view)
        self.view.reset()
                
        self.coeff_view.clear()
        
        self.build_actualisation_groups()
        if self.coeffs_df is not None:
            df = self.coeffs_df.reset_index(drop=True)
            self.coeff_view.set_dataframe(df)
        self.coeff_view.reset()
        
        

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
#        for varname in self.frame_vars_list:
#            table = self.inputs.table
#            target = self.frame.get_value(varname, "cible") 
#            if varname in table:
                
        df = self.coeffs_df
        table = self.inputs.table
        
        for coeff, varname in self.actualisation_vars.iteritems():
            inflator = df.get_value(coeff, "value") 
            if varname in table:
                table[varname] = inflator*table[varname]

        self.parent().emit(SIGNAL('inflated()'))

        QDialog.accept(self)


if __name__=='__main__':
    import sys
    import numpy as np

    app = QApplication(sys.argv)
    widget = InflationWidget()
    widget.show()
    filename = "../france/data/actualisation_groups.h5"
#    widget.build_actualisation_groups(filename)
    widget.set_targets_from_file(filename)
    app.exec_()



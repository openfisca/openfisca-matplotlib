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
from numpy import logical_not, unique
from pandas import read_csv, DataFrame, concat

from PyQt4.QtCore import SIGNAL, Qt, QSize 
from PyQt4.QtGui import (QLabel, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, 
                         QSpinBox, QDoubleSpinBox, QCheckBox, QInputDialog, QFileDialog, 
                         QMessageBox, QApplication, QCursor, QSpacerItem, QSizePolicy,
                         QDialogButtonBox)
from core.qthelpers import MyComboBox, MySpinBox, MyDoubleSpinBox, DataFrameViewWidget, _fromUtf8, get_icon
from widgets.matplotlibwidget import MatplotlibWidget
from Config import CONF
from core.columns import EnumCol, BoolCol, AgesCol, DateCol, BoolPresta, IntPresta
from core.calmar import calmar

MODCOLS = [EnumCol, BoolCol, BoolPresta, IntPresta, AgesCol, DateCol]

class CalibrationWidget(QDialog):
    def __init__(self,  inputs, outputs = None, parent = None):
        super(CalibrationWidget, self).__init__(parent)

        self.aggregate_calculated = False

        if outputs:
            self.aggregate_calculated = True

        self.param = {}
        self.inputs = None
        self.frame = None
        self.input_margins_df = None
        self.output_margins_df   = None

        self.totalpop = None
        self.ini_totalpop = 0
        
        ## Create geometry
        self.setWindowTitle("Calibration")
        self.setObjectName("Calibration")

        # Parameters widgets
        up_spinbox      = MyDoubleSpinBox(self, 'Ratio maximal','','',min_=1, max_=100, step=1, value = CONF.get('calibration', 'up'), changed = self.set_param)
        invlo_spinbox   = MyDoubleSpinBox(self, 'Inverse du ratio minimal','','',min_=1, max_=100, step=1, value = CONF.get('calibration', 'invlo'), changed = self.set_param)                 
        method_choices  = [(u'Linéaire', 'linear'),(u'Raking ratio', 'raking ratio'), (u'Logit', 'logit')]
        method_combo     = MyComboBox(self, u'Choix de la méthode', method_choices)
        self.param_widgets = {'up': up_spinbox.spin, 'invlo': invlo_spinbox.spin, 'method': method_combo.box}        

        # Total population widget
        self.ini_totalpop_label = QLabel("", parent = self) 
        self.pop_checkbox = QCheckBox(u"Ajuster", self)
        self.pop_spinbox = MySpinBox(self, u" Cible :", "", option = None ,min_=15e6, max_=30e6, step=5e6, changed = self.set_totalpop)
        self.pop_spinbox.setDisabled(True)

        
        # Margins table view
        self.view = DataFrameViewWidget(self)
        
        # Add/Remove margin button         

        save_btn = self.add_toolbar_btn(tooltip = u"Sauvegarder les paramètres et cales actuels",
                                        icon = "document-save.png")
        
        open_btn = self.add_toolbar_btn(tooltip = u"Ouvrir des paramètres",
                                        icon = "document-open.png")

        add_var_btn  = self.add_toolbar_btn(tooltip = u"Ajouter une variable de calage",
                                        icon = "list-add.png")
        
        rmv_var_btn = self.add_toolbar_btn(tooltip = u"Retirer une variable de calage",
                                        icon = "list-remove.png")
        
        rst_var_btn = self.add_toolbar_btn(tooltip = u"Retirer toutes les variables de calage",
                                        icon = "view-refresh.png")

        self.calibrate_btn = self.add_toolbar_btn(tooltip = u"Lancer le calage",
                                             icon = "calculator_red.png")
        self.calibrate_btn.setDisabled(True)
        
        toolbar_btns = [save_btn, open_btn, add_var_btn, rmv_var_btn, rst_var_btn, self.calibrate_btn]
        toolbar_lyt = QHBoxLayout()

        for btn in toolbar_btns:
            toolbar_lyt.addWidget(btn)
        # Build layouts
        calib_lyt = QHBoxLayout()
        calib_lyt.addLayout(toolbar_lyt)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        for w in [spacerItem, up_spinbox, invlo_spinbox, method_combo]:
            if isinstance(w, QSpacerItem):
                calib_lyt.addItem(w)
            else:
                calib_lyt.addWidget(w)

        verticalLayout = QVBoxLayout(self)
        verticalLayout.addLayout(calib_lyt)

        totalpop_lyt = QHBoxLayout()
        for w in [self.ini_totalpop_label, 
                  self.pop_checkbox, self.pop_spinbox]:
            totalpop_lyt.addWidget(w)
        verticalLayout.addLayout(totalpop_lyt)
        verticalLayout.addWidget(self.view)

        # weights ratio plot        
        self.mplwidget = MatplotlibWidget(self)
        verticalLayout.addWidget(self.mplwidget)

        
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel| QDialogButtonBox.Ok, parent = self)
        verticalLayout.addWidget(button_box)


        # Connect signals
        self.connect(method_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_param)        
        self.connect(self.pop_checkbox, SIGNAL('clicked()'), self.set_totalpop)
        self.connect(save_btn, SIGNAL('clicked()'), self.save_config)
        self.connect(open_btn, SIGNAL('clicked()'), self.load_config)
        self.connect(add_var_btn, SIGNAL('clicked()'), self.add_var)
        self.connect(rmv_var_btn, SIGNAL('clicked()'), self.rmv_var)
        self.connect(rst_var_btn, SIGNAL('clicked()'), self.rst_var)
        self.connect(self.calibrate_btn, SIGNAL('clicked()'), self.calibrate)
        self.connect(button_box, SIGNAL('accepted()'), self.accept);
        self.connect(button_box, SIGNAL('rejected()'), self.reject);

#        self.connect(self, SIGNAL('param_or_margins_changed()'), self)


        self.init_totalpop()
        self.set_inputs(inputs)                
        self.init_param()
        self.set_inputs_margins_from_file()
        self.outputs = outputs
    
    def add_toolbar_btn(self, tooltip = None, icon = None):
        btn = QPushButton(self)
        if tooltip:
            btn.setToolTip(tooltip)
        if icon:
            icn = get_icon(icon)
            btn.setIcon(icn)
            btn.setIconSize(QSize(22, 22))
        return btn
        
    def init_totalpop(self):
        if self.totalpop:
            self.pop_checkbox.setChecked(True)
            self.pop_spinbox.setEnabled(True)
            self.pop_spinbox.spin.setEnabled(True)
            self.pop_spinbox.spin.setValue(self.totalpop)
        else:
            self.pop_checkbox.setChecked(False)
            self.pop_spinbox.setDisabled(True)
            self.pop_spinbox.spin.setDisabled(True)

    def set_inputs(self, inputs):
        self.inputs = inputs
        self.unit = 'men'
        self.weights = 1*self.inputs.get_value("wprm", inputs.index[self.unit])
        self.weights_init = self.inputs.get_value("wprm_init", inputs.index[self.unit])
        self.champm =  self.inputs.get_value("champm", self.inputs.index[self.unit])
        
        self.ini_totalpop = sum(self.weights_init*self.champm)
        label_str = u"Population initiale totale :" + str(int(round(self.ini_totalpop))) + u" ménages"
        self.ini_totalpop_label.setText(label_str)

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

    
    def set_inputs_margins_from_file(self, filename = None, year = None):
        if year is None:
            year     = str(CONF.get('simulation','datesim').year)
        if filename is None:
            fname    = CONF.get('calibration','inputs_filename')
            data_dir = CONF.get('paths', 'data_dir')
            filename = os.path.join(data_dir, fname)
        self.set_margins_from_file(filename, year, source="input")
        self.init_totalpop()
    
    def add_var(self, source = 'free'):
        '''
        Adds a variable to the margins
        source can be 'free' (default), 'input' or 'output'
        '''
#        if   result == "add_input_margin" : self.add_input_margin()
#        elif result == "add_output_margin": self.add_output_margin()
        lists      = {'input': self.input_vars_list, 'output': self.output_vars_list, 'free': self.free_vars_list}        
        
        variables_list = lists[source]
        varnames = self.get_name_label_dict(variables_list) # {varname: varlabel}
        
        varlabel, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                           sorted(varnames.keys()))
        
        insertion = ok and not(varlabel.isEmpty()) and (varlabel in sorted(varnames.keys()))
        if insertion:
            varname = varnames[varlabel]
            datatable_name = self.get_var_datatable(varname)
            target = None
            if source=='input' and self.input_margins_df:
                index = self.input_margins_df.index
                indices = [ (var, mod)  for (var, mod) in index if var==varname ]
                target_df = (self.input_margins_df['target'][indices]).reset_index()
                target = dict(zip(target_df['mod'] ,target_df['target']))
            else:
                if datatable_name =='outputs':
                    varcol = self.outputs.description.get_col(varname)
                elif datatable_name =='inputs':
                    varcol = self.inputs.description.get_col(varname) 
                
                if varcol.__class__ not in MODCOLS:
                        val, ok = QInputDialog.getDouble(self.parent(), "Valeur de la  marge", unicode(varlabel) + "  (millions d'euros)")
                        if ok:
                            target = {str(varname): val*1e6}
                else:
                    if datatable_name =='outputs':
                        idx = self.outputs.index[self.unit]
                        unique_values = unique(self.outputs.get_value(varname, idx))
                    elif datatable_name =='inputs':
                        idx = self.inputs.index[self.unit]
                        unique_values = unique(self.inputs.get_value(varname, idx))
                    target = {}
                    
                    for mod in unique_values:
                        val, ok = QInputDialog.getDouble(self.parent(), "Valeur de la  marge", unicode(varlabel) + u" pour la modalité " + str(mod) )
                        if ok:
                            target[mod] = val
                        else:
                            return
                    
            if target:
                self.add_var2(varname, target = target, source=source)
                self.param_or_margins_changed()
        
    def rmv_var(self):
        '''
        Removes variable from the margins
        '''
        vars_in_table = self.frame['var'].unique() 
        varnames = self.get_name_label_dict(vars_in_table)        
        varlabel, ok = QInputDialog.getItem(self.parent(), "Ajouter une variable", "Nom de la variable", 
                                           sorted(varnames.keys()))
        varname = varnames[varlabel]
        deletion = ok and not(varlabel.isEmpty())
        if deletion:
            df =  self.frame.reset_index(drop=True)
            cleaned = df[df['var'] != varname]
            self.frame = cleaned 
        self.param_or_margins_changed()
        
    def rst_var(self):
        '''
        Removes all variables from the margins
        '''
        self.frame = None
        self.pop_checkbox.setChecked(False)        
        self.pop_spinbox.setDisabled(True)
        self.pop_spinbox.spin.setDisabled(True)
        self.set_totalpop()
        self.plotWeightsRatios()

    @property
    def table_vars_list(self):
        '''
        List of the variables appearing in the table (and the dataframe)
        '''
        if self.frame:
            df = self.frame
            if 'var' in df.columns: 
                return list(df['var'].unique())
        else:
            return []
    
    @property
    def input_vars_list(self):
        '''
        List of the input variable with available margins
        '''
        if self.input_margins_df:
            df = self.input_margins_df.reset_index()
            #  TODO 'config' 
            set_ic = set(df['var'].unique())
            lic = set_ic.intersection( set(self.inputs.description.col_names))
            return sorted(list(lic - set(self.table_vars_list)))
        else:
            return []
    
    @property
    def free_vars_list(self):
        '''
        Builds the sorted list of all accessible variables
        '''
        outset = set(self.inputs.col_names) - set(self.table_vars_list)
        if self.aggregate_calculated:
            outset = outset.union(set(self.outputs.col_names)) - set(self.table_vars_list)
        return sorted(list(outset))
    
    @property
    def output_vars_list(self):
        if self.output_margins_df is not None:
            df = self.output_margins_df.reset_index() 
            #   data_oc = df[ df['source'] == 'output'] # + df['source'] == 'config']
            set_oc = set(df['var'].unique())
            loc = set_oc.intersection( set(self.outputs.col_names))
            return sorted(list(loc - set(self.table_vars_list)))
        else:
            return []
    
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

    def param_or_margins_changed(self):
        self.calibrate_btn.setEnabled(True)
        self.update_view()
        self.emit(SIGNAL('param_or_margins_changed()'))
        
    def update_view(self):
        self.view.clear()
        if self.frame is not None:
            df = self.frame.reset_index(drop=True)
            df_view = df[ ["var", u"modalités", "cible", u"cible ajustée", "marge", "marge initiale", "variable" ]]            
            self.view.set_dataframe(df_view)
        self.view.reset()
        self.plotWeightsRatios()   
                                        
    def add_var2(self, varname, target=None, source = 'free'):
        '''
        Add a variable in the dataframe
        '''
        w_init = self.weights_init*self.champm
        w = self.weights*self.champm

        varcol = self.get_col(varname)
        idx = self.inputs.index[self.unit]
        enum = self.inputs.description.get_col('qui'+self.unit).enum
        people = [x[1] for x in enum]

        if self.inputs.description.has_col(varname):
            value = self.inputs.get_value(varname, index = idx)
        elif self.outputs.description.has_col(varname):
            value = self.outputs.get_value(varname, index = idx, opt = people, sum_ = True)

        label = varcol.label
        # TODO: rewrite this using pivot table
        items = [ ('marge'    , w[self.champm]  ), ('marge initiale' , w_init[self.champm] )]        
        if varcol.__class__  in MODCOLS:
            items.append(('mod',   value[self.champm]))
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
                print "modalities"
                print mods
                print "targets"
                print target.keys()
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
        elif isinstance(varcol, IntPresta):
            res[u'modalités'] = mods
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

             
    def set_param(self):
        '''
        Set parameters from box widget values
        '''
        for parameter, widget in self.param_widgets.iteritems():
            if isinstance(widget, QComboBox):
                data = widget.itemData(widget.currentIndex())                
                self.param[parameter] = unicode(data.toString())
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                self.param[parameter] = widget.value()
        self.param_or_margins_changed()        
        return True
                
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


    def build_calmar_data(self, marges, weights_in):
        '''
        Builds the data dictionnary used as calmar input argument
        '''
        
        # Select only champm ménages by nullifying weght for irrelevant ménages
        
        data = {weights_in: self.weights_init*self.champm}
        for var in marges:
            if self.inputs.description.has_col(var):
                data[var] = self.inputs.get_value(var, self.inputs.index[self.unit])
            else:
                if self.outputs:
                    if self.outputs.description.has_col(var):
                        idx = self.outputs.index[self.unit]
                        enum = self.inputs.description.get_col('qui'+self.unit).enum
                        people = [x[1] for x in enum]
                        data[var] = self.outputs.get_value(var, index=idx, opt=people, sum_=True)        
        return data

    
    def update_weights(self, marges, param = {}, weights_in='wprm_init'):
        '''
        Lauches calmar, stores new weights and returns adjusted margins
        '''
        data = self.build_calmar_data(marges, weights_in)
        try:
            val_pondfin, lambdasol, marge_new = calmar(data, marges, param = param, pondini=weights_in)
        except Exception, e:
            raise Exception("Calmar returned error '%s'" % e)

        # Updating only champm weights
        self.weights = val_pondfin*self.champm + self.weights*(logical_not(self.champm))
        return marge_new    
    
    def calibrate(self):
        '''
        Calibrate accoding to margins found in frame
        '''
        if self.frame is None and self.totalpop is None:
            self.update_view()
            return


        df = self.frame
        inputs = self.inputs
        margins = {}
        
        if df is not None:
            df = df.reset_index(drop=True)
            df = df.set_index(['var','mod'], inplace = True)        
            for var, mod in df.index:
                # Dealing with non categorical vars ...
                if df.get_value((var,mod), u"modalités") == 'total':
                    margins[var] =  df.get_value((var,mod), 'cible')
                #  ... and categorical vars
                else:
                    if not margins.has_key(var):
                        margins[var] = {}
                    margins[var][mod] =  df.get_value((var,mod), 'cible')
                
        param = self.get_param()

        if self.totalpop is not None:
            margins['totalpop'] = self.totalpop
        adjusted_margins = self.update_weights(margins, param=param)
        
        if 'totalpop' in margins.keys():
            del margins['totalpop']
        
        w = self.weights
        for var in margins.keys():
            if inputs.description.has_col(var):
                value = inputs.get_value(var, inputs.index[self.unit])
            else:
                idx = self.outputs.index[self.unit]
                enum = self.outputs._inputs.description.get_col('qui'+self.unit).enum
                people = [x[1] for x in enum]
                value = self.outputs.get_value(var, index=idx, opt=people, sum_=True)
                
            if isinstance(margins[var], dict):
                items = [('marge', w  ),('mod', value)]
                updated_margins = DataFrame.from_items(items).groupby('mod', sort= True).sum()                
                for mod in margins[var].keys():
                    df.set_value((var,mod), u"cible ajustée", adjusted_margins[var][mod])
                    df.set_value((var,mod), u"marge", updated_margins['marge'][mod])
            else:
                updated_margin = (w*value).sum()
                df.set_value((var,0), u"cible ajustée", adjusted_margins[var])
                df.set_value((var,0), u"marge", updated_margin)
        
        if self.frame is not None:
            self.frame = df.reset_index()
        self.update_view()
        self.calibrate_btn.setDisabled(True)
                    
    def plotWeightsRatios(self):
        ax = self.mplwidget.axes
        ax.clear()
        weight_ratio = self.weights/self.weights_init
        ax.hist(weight_ratio, 50, normed=1, histtype='stepfilled')
        ax.set_xlabel(u"Poids relatifs")
        ax.set_ylabel(u"Densité")
        self.mplwidget.draw()
        
    def set_margins_from_file(self, filename, year, source):
        '''
        Sets margins for inputs variable from file
        '''
        with open(filename) as f_tot:
            totals = read_csv(f_tot,index_col = (0,1))
        # if data for the configured year is not availbale leave margins empty
        if year not in totals:
            return
        marges = {}
        if source == 'input':
            self.input_margins_df = DataFrame({'target':totals[year]})
        elif source =='output':
            self.output_margins_df = DataFrame({'target':totals[year]})
            
        for var, mod in totals.index:
            if not marges.has_key(var):
                marges[var] = {}
            marges[var][mod] =  totals.get_value((var,mod),year)
            
        for var in marges.keys():
            if var == 'totalpop': 
                if source == "input" or source == "config" :
                    totalpop = marges.pop('totalpop')[0]
                    marges['totalpop'] = totalpop
                    self.totalpop = totalpop
            else:
                self.add_var2(var, marges[var], source = source)

    def get_name_label_dict(self, variables_list):
        '''
        Builds a dict with label as keys and varname as value
        '''
        varnames = {}
        for varname in variables_list:
            varcol = self.get_col(varname)
            if varcol:
                if varcol.label:
                    varnames[_fromUtf8(varcol.label)] = varname
                else:
                    varnames[_fromUtf8(varname)] = varname
            
        return varnames
    
    def get_col(self, varname):
        '''
        Looks for a column in inputs description, then in outputs description
        '''
        if self.inputs.description.has_col(varname):
            return self.inputs.description.get_col(varname)
        elif self.outputs.description.has_col(varname):
            return self.outputs.description.get_col(varname)
        else:
            print "Variable %s is absent from both inputs and outputs" % varname
            return None

    def get_var_datatable(self, varname):
        if self.inputs.description.has_col(varname):
            return 'inputs'
        elif self.outputs.description.has_col(varname):
            return 'outputs'
        else:
            print "Variable %s is absent from both inputs and outputs" % varname
            return ''

    def save_config(self):
        '''
        Save calibration parameters
        '''
        # TODO: add  param
        # param_dict = self.get_param()
        year     = str(CONF.get('simulation','datesim').year)
        df = self.frame
        
        if df is None:
            QMessageBox.critical(
                self, "Erreur", u"La table est vide" ,
                QMessageBox.Ok, QMessageBox.NoButton)
            return 
        
        if df is not None:  
            if len(df['var']) == 0:
                QMessageBox.critical(
                    self, "Erreur", u"Les marges sont vides" ,
                    QMessageBox.Ok, QMessageBox.NoButton)
                return

        pop = DataFrame(data ={'var' : ['totalpop'],
                               'mod' : [0],
                               year  : [self.totalpop]})
        df = self.frame.copy()
        df[year] = df['cible']
        saved = df[['var','mod',year]]
        saved = saved.append(pop, ignore_index=True)
        saved = DataFrame(data =saved, columns =['var','mod',year] ) # reorder the columns !                
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
        self.reset()
        calib_dir = CONF.get('paths','calib_dir')
        fileName  = QFileDialog.getOpenFileName(self,
                                               u"Ouvrir un calage", calib_dir, u"Calages OpenFisca (*.csv)")
        # TODO: should read the date from the calibration file
        year      = str(CONF.get('simulation','datesim').year)

        if fileName:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.set_margins_from_file(fileName, year = year, source='config')
            self.init_totalpop()
            QApplication.restoreOverrideCursor()    
            self.param_or_margins_changed()

    def accept(self):
        '''
        Updates inputs weights and close dialog
        '''
        self.inputs.set_value('wprm', self.weights, self.inputs.index[self.unit])
        self.inputs.propagate_to_members( unit=self.unit, col = 'wprm')
        self.parent().emit(SIGNAL('weights_changed()'))

        QDialog.accept(self)

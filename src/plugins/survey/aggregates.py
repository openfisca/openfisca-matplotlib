# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division
from pandas import DataFrame
import os 
from numpy import nan         
from datetime import datetime
from pandas import ExcelWriter


from src.qt.QtGui import (QWidget, QVBoxLayout,
                         QApplication, QCursor, QSizePolicy, QMenu,
                         QGroupBox, QFileDialog, QMessageBox)
from src.qt.QtCore import SIGNAL, Qt

from src.core.config import CONF, get_icon
from src.core.qthelpers import OfSs, DataFrameViewWidget, create_action, add_actions

from src import SRC_PATH
from src.core.simulation import SurveySimulation

from src.plugins import OpenfiscaPluginWidget, PluginConfigPage
from src.core.baseconfig import get_translation
_ = get_translation("src")

    
class Aggregates(object):
    def __init__(self):
        super(Aggregates, self).__init__()

        self.simulation = None

        self.simulation = None
        self.data = None
        self.data_default = None
        self.totals_df = None
        self.set_default_var_list()
        self.set_header_labels()
        self.show_default = False
        self.show_real = True
        self.show_diff = True

    def set_default_var_list(self):
        self.varlist = ['cotsoc_noncontrib', 'csg', 'crds',
            'irpp', 'ppe',
            'af', 'af_base', 'af_majo','af_forf', 'cf',
            'paje_base', 'paje_nais', 'paje_colca', 'paje_clmg',
            'ars', 'aeeh', 'asf', 'aspa',
            'aah', 'caah', 
            'rsa', 'rsa_act', 'aefa', 'api',
            'logt', 'alf', 'als', 'apl']

    def set_header_labels(self):
        '''
        Sets headers labels
        '''
        self.var_label           = u"Mesure"
        self.unit_label          = u"Unité"
        self.dep_label           = u"Dépense\n(millions d'€)" 
        self.benef_label         = u"Bénéficiaires\n(milliers)"
        self.dep_default_label   = u"Dépense initiale\n(millions d'€)"
        self.benef_default_label = u"Bénéficiaires\ninitiaux\n(milliers)"
        self.dep_real_label      = u"Dépenses\nréelles\n(millions d'€)"
        self.benef_real_label    = u"Bénéficiaires\nréels\n(milliers)"
        self.dep_diff_abs_label      = u"Diff. absolue\nDépenses\n(millions d'€) "
        self.benef_diff_abs_label    = u"Diff absolue\nBénéficiaires\n(milliers)"
        self.dep_diff_rel_label      = u"Diff. relative\nDépenses"
        self.benef_diff_rel_label    = u"Diff. relative\nBénéficiaires"
        
        
    def set_simulation(self, simulation):
        
        if isinstance(simulation, SurveySimulation):
            self.simulation = simulation
        else:
            raise Exception('Aggregates:  %s should be an instance of %s class'  %(simulation, SurveySimulation))
          
    def set_data(self):
        """
        Generates aggregates at the household level ('men') and get weights
        """
        self.data, self.data_default = self.simulation.aggregated_by_household(self.varlist)
        self.wght = self.data['wprm']

    def compute(self):
        self.set_data()
        self.compute_aggregates()
        self.load_amounts_from_file()
        self.compute_real()
        self.compute_diff()


    def compute_aggregates(self):
        '''
        Compute aggregate amounts
        '''
        V  = []    
        M = {'data': [], 'default': []}
        B = {'data': [], 'default': []}
        U = []

        M_label = {'data': self.dep_label, 
                   'default': self.dep_default_label}
        B_label = {'data': self.benef_label, 
                   'default': self.benef_default_label}

        description = self.simulation.outputs.description
        label2var, var2label, var2enum = description.builds_dicts()
        for var in self.varlist:
            # amounts and beneficiaries from current data and default data if exists
            montant_benef = self.get_aggregate(var)
            V.append(var2label[var])
                        
            try:
                varcol  = description.get_col(var)
                unit = varcol._unit
            except:
                unit = 'NA'
                 
            U.append(unit)
            for dataname in montant_benef:
                M[dataname].append( montant_benef[dataname][0] )
                B[dataname].append( montant_benef[dataname][1] )
        
        # build items list
        items = [(self.var_label, V)]

        for dataname in M:
            if M[dataname]:
                items.append( (M_label[dataname], M[dataname]))
                items.append(  (B_label[dataname], B[dataname]) )

        items.append( (self.unit_label, U) )        
        self.aggr_frame = DataFrame.from_items(items)

    def get_aggregate(self, var):
        '''
        Returns aggregate spending, nb of beneficiaries
        '''
        datasets = {'data': self.data}
        m_b = {}
        
        if self.data_default is not None:
            datasets['default'] = self.data_default

        for name, data in datasets.iteritems():
            montants = data[var]
            beneficiaires = data[var].values != 0
            m_b[name] = [int(round(sum(montants*self.wght)/10**6)),
                        int(round(sum(beneficiaires*self.wght)/10**3))]
        return m_b


    def compute_real(self):
        '''
        Adds administrative data to dataframe
        '''
        if self.totals_df is None:
            return    
        A, B = [], []
        for var in self.varlist:
            # totals from administrative data        
            if var in self.totals_df.index:
                A.append(self.totals_df.get_value(var, "amount"))
                B.append(self.totals_df.get_value(var, "benef"))
            else:
                A.append(nan)
                B.append(nan)
        self.aggr_frame[self.dep_real_label] = A
        self.aggr_frame[self.benef_real_label] = B

        
    def compute_diff(self):
        '''
        Computes and adds relative differences
        '''
        dep   = self.aggr_frame[self.dep_label]
        benef = self.aggr_frame[self.benef_label]
        
        if self.show_default:
            ref_dep_label, ref_benef_label = self.dep_default_label, self.benef_default_label
            if ref_dep_label not in self.aggr_frame:
                return
        elif self.show_real:
            ref_dep_label, ref_benef_label = self.dep_real_label, self.benef_real_label
        else:
            return
        
        ref_dep = self.aggr_frame[ref_dep_label]   
        ref_benef = self.aggr_frame[ref_benef_label]
                    
        self.aggr_frame[self.dep_diff_rel_label] = (dep-ref_dep)/abs(ref_dep)
        self.aggr_frame[self.benef_diff_rel_label] = (benef-ref_benef)/abs(ref_benef)
        self.aggr_frame[self.dep_diff_abs_label] = (dep-ref_dep)
        self.aggr_frame[self.benef_diff_abs_label] = (benef-ref_benef)
        
    def load_amounts_from_file(self, filename = None, year = None):
        '''
        Loads totals from files
        '''
        from pandas import HDFStore
        if year is None:
            year     = self.simulation.datesim.year
        if filename is None:
            country = self.simulation.country
            data_dir = os.path.join(SRC_PATH, country, 'data')

        try:
            filename = os.path.join(data_dir, "amounts.h5")
            store = HDFStore(filename)
    
            df_a = store['amounts']
            df_b = store['benef']
            store.close()
            self.totals_df = DataFrame(data = { "amount" : df_a[year]/10**6, "benef": df_b[year]/1000 } )
            row = DataFrame({'amount': nan, 'benef': nan}, index = ['logt']) 
            self.totals_df = self.totals_df.append(row)

            # Add some aditionnals totals
            for col in ['amount', 'benef']:
                
                # Deals woth logt
                logt = 0
                for var in ['apl', 'alf', 'als']:
                    logt += self.totals_df.get_value(var, col)
                self.totals_df.set_value('logt', col,  logt)
                
                # Deals wit irpp, csg, crds
                for var in ['irpp', 'csg', 'crds']:
                    if col in ['amount']:
                        val = - self.totals_df.get_value(var, col)
                        self.totals_df.set_value(var, col, val)
                    
        except:
            #  raise Exception(" No administrative data available for year " + str(year))
            import warnings
            warnings.warn(" No administrative data available for year %s in file %s" %( str(year), filename)) 
            self.totals_df = None
            return
        
    def save_table(self, directory = None, filename = None, table_format = None):
        '''
        Saves the table to some format
        '''    
        now = datetime.now()
        if table_format is None:
            if filename is not None:
                extension = filename[-4:]
                if extension == '.xls':
                    table_format = 'xls'
                elif extension == '.csv':
                    table_format = 'csv'
            else:       
                table_format = 'xls'
        
        if directory is None:
            directory = "."
        if filename is None:
            filename = 'Aggregates_%s.%s' % (now.strftime('%d-%m-%Y'), table_format)
        
        fname = os.path.join(directory, filename)

        try:
            df = self.aggr_frame
            if table_format == "xls":
                writer = ExcelWriter(str(fname))
                df.to_excel(writer, "aggregates", index= False, header= True)
                descr = self.create_description()
                descr.to_excel(writer, "description", index = False, header=False)
                writer.save()
            elif table_format =="csv":
                df.to_csv(fname, "aggregates", index= False, header = True)
                         
        except Exception, e:
                raise Exception("Aggregates: Error saving file", str(e))

            
    def create_description(self):
        '''
        Creates a description dataframe
        '''
        now = datetime.now()
        descr =  [u'OpenFisca', 
                         u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M')),
                         u'Système socio-fiscal au %s' % self.simulation.datesim,
                         u"Données d'enquêtes de l'année %s" %str(self.simulation.survey.survey_year) ]
        return DataFrame(descr)
        
    
    def clear(self):
        self.data = None
        self.data_default = None
        self.totals_df = None
        
        
class AggregatesConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Aggregates")
        
    def setup_page(self):

        export_group = QGroupBox(_("Export"))
        export_dir = self.create_browsedir(_("Export directory"), "table/export_dir")
        choices = [('cvs', 'csv'),
                   ('xls', 'xls'),]
        table_format = self.create_combobox(_('Table export format'), choices, 'table/format') 
        export_layout = QVBoxLayout()
        export_layout.addWidget(export_dir)
        export_layout.addWidget(table_format)
        export_group.setLayout(export_layout)

        variables_group = QGroupBox(_("Columns")) 
        show_dep = self.create_checkbox(_("Display expenses"),
                                        'show_dep')
        show_benef = self.create_checkbox(_("Display beneficiaries"),
                                        'show_benef')
        show_real = self.create_checkbox(_("Display actual values"),
                                        'show_real')
        show_diff = self.create_checkbox(_("Display differences"),
                                        'show_diff')
        show_diff_rel = self.create_checkbox(_("Display relative differences"),
                                        'show_diff_rel')
        show_diff_abs = self.create_checkbox(_("Display absolute differences"),
                                        'show_diff_abs')                
        show_default = self.create_checkbox(_("Display default values"),
                                        'show_default')

        variables_layout = QVBoxLayout()
        for combo in [show_dep, show_benef, show_real, show_diff, show_diff_abs,
                       show_diff_rel, show_default]:
            variables_layout.addWidget(combo)
        variables_group.setLayout(variables_layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(export_group)
        vlayout.addWidget(variables_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)

class AggregatesWidget(OpenfiscaPluginWidget):
    """
    Aggregates Widget
    """
    CONF_SECTION = 'aggregates'
    CONFIGWIDGET_CLASS = AggregatesConfigPage

    def __init__(self, parent = None):
        super(AggregatesWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName(u"Aggrégats")
        self.setWindowTitle(u"Aggrégats")
        self.dockWidgetContents = QWidget()
        
        self.view = DataFrameViewWidget(self.dockWidgetContents)

        # Context Menu         
        headers = self.view.horizontalHeader()  
        self.headers = headers
        headers.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.headers,SIGNAL('customContextMenuRequested(QPoint)'), self.ctx_select_menu)
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.view)
        self.setLayout(verticalLayout)
        
        # Initialize attributes
        self.survey_year = None
        self.parent = parent
        self.aggregates = None

        self.show_dep = True
        self.show_benef = True        
        self.show_real = True
        self.show_diff = True
        self.show_diff_abs = True
        self.show_diff_rel = True
        self.show_default = False
        
    def set_aggregates(self, aggregates):
        """
        Sets aggregates
        """
        self.aggregates = aggregates
        if self.aggregates.simulation.reforme is False:
            self.show_default = False
        else:
            self.show_default = True

    def ctx_select_menu(self, point):
        self.select_menu.exec_( self.headers.mapToGlobal(point) )

    def toggle_show_default(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_default = boolean
        self.update_view()

    def toggle_show_real(self, boolean):
        ''' 
        Toggles reference values from administrative data
        '''
        self.show_real = boolean
        self.update_view()
            
    def toggle_show_diff_abs(self, boolean):
        ''' 
        Toggles differences 
        '''
        self.show_diff_abs = boolean
        self.update_view()

    def toggle_show_diff_rel(self, boolean):
        ''' 
        Toggles differences 
        '''
        self.show_diff_rel = boolean
        self.update_view()

    def toggle_show_dep(self, boolean):
        '''
        Toggles to show amounts (dépenses) 
        '''
        self.show_dep = boolean
        self.update_view()
        
    def toggle_show_benef(self, boolean):
        '''
        Toggles to show beneficiaries
        ''' 
        self.show_benef = boolean
        self.update_view()
        
        
    def update_view(self):
        '''
        Update aggregate amounts view
        '''
        if self.aggregates.aggr_frame is None:
            return
            
        cols = [self.aggregates.var_label, self.aggregates.unit_label,
                self.aggregates.dep_label, self.aggregates.dep_default_label, self.aggregates.dep_real_label, 
                self.aggregates.dep_diff_abs_label, self.aggregates.dep_diff_rel_label, 
                self.aggregates.benef_label, self.aggregates.benef_default_label, self.aggregates.benef_real_label,
                self.aggregates.benef_diff_abs_label, self.aggregates.benef_diff_rel_label]
        
        if not self.show_real:
            cols.remove(self.aggregates.dep_real_label) 
            cols.remove(self.aggregates.benef_real_label)

        if not self.show_default:
            cols.remove(self.aggregates.dep_default_label)
            cols.remove(self.aggregates.benef_default_label)
            

        remove_all_diffs =  not (self.aggregates.show_real or self.aggregates.show_default)
        if not remove_all_diffs:
            self.aggregates.compute_diff()
        
        if (not self.show_diff_abs) or remove_all_diffs:
            cols.remove(self.aggregates.dep_diff_abs_label)
            cols.remove(self.aggregates.benef_diff_abs_label)    
        
        if (not self.show_diff_rel) or remove_all_diffs: 
            cols.remove(self.aggregates.dep_diff_rel_label)
            cols.remove(self.aggregates.benef_diff_rel_label)
 
        if not self.show_dep:
            for label in [self.aggregates.dep_label, self.aggregates.dep_real_label, self.aggregates.dep_default_label, self.aggregates.dep_diff_abs_label, self.aggregates.dep_diff_rel_label]:
                if label in cols:
                    cols.remove(label)

        if not self.show_benef:
            for label in [self.aggregates.benef_label, self.aggregates.benef_real_label, self.aggregates.benef_default_label, self.aggregates.benef_diff_abs_label, self.aggregates.benef_diff_rel_label]:
                if label in cols:
                    cols.remove(label)
        self.view.set_dataframe(self.aggregates.aggr_frame[cols])
        self.view.resizeColumnsToContents()
        self.view.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

                
    def calculated(self):
        '''
        Emits signal indicating that aggregates are computed
        '''
        self.emit(SIGNAL('calculated()'))
                
    
    def clear(self):
        self.view.clear()
         
        
    def save_table(self, table_format = None):
        '''
        Saves the table to the designated format
        '''
        if table_format is None:
            table_format = self.get_option('table/format')
         
        output_dir = self.get_option('table/export_dir')
        filename = 'sans-titre.' + table_format
        user_path = os.path.join(output_dir, filename)

        extension = table_format.upper() + "   (*." + table_format + ")"
        fname = QFileDialog.getSaveFileName(self,
                                               _("Save table"), #"Exporter la table", 
                                               user_path, extension)
        
        if fname:
            self.set_option('table/export_dir', os.path.dirname(str(fname)))
            try:
                df = self.view.model().dataframe
                if table_format == "xls":
                    writer = ExcelWriter(str(fname))
                    df.to_excel(writer, "aggregates", index= False, header= True)
                    descr = self.create_description()
                    descr.to_excel(writer, "description", index = False, header=False)
                    writer.save()
                elif table_format =="csv":
                    df.to_csv(writer, "aggregates", index= False, header = True)
                     
                
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
        return "Aggregates"

    
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
        Update aggregate outputs and refresh view
        '''
        
        simulation = self.main.survey_simulation
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        agg = Aggregates()
        agg.set_simulation(simulation)
        agg.compute()
        
        self.aggregates = agg
        self.survey_year = self.aggregates.simulation.survey.survey_year
        self.description = self.aggregates.simulation.outputs.description

        self.select_menu = QMenu()
        action_dep     = create_action(self, u"Dépenses",   toggled = self.toggle_show_dep)
        action_benef     = create_action(self, u"Bénéficiaires", toggled = self.toggle_show_benef)
        action_real    = create_action(self, u"Réel",       toggled = self.toggle_show_real)
        action_diff_abs    = create_action(self, u"Diff. absolue", toggled = self.toggle_show_diff_abs)
        action_diff_rel    = create_action(self, u"Diff. relative ", toggled = self.toggle_show_diff_rel)
        action_default = create_action(self, u"Référence",  toggled = self.toggle_show_default)
                
        actions = [action_dep, action_benef]        
        action_dep.toggle()
        action_benef.toggle()
                
        if self.aggregates.simulation.reforme is False:
            self.show_default = False
            if self.aggregates.totals_df is not None: # real available
                actions.append(action_real)
                actions.append(action_diff_abs)
                actions.append(action_diff_rel)
                action_real.toggle()
                action_diff_abs.toggle()
                action_diff_rel.toggle()
            else: 
                self.show_real = False
                self.show_diff_abs = False
                self.show_diff_rel = False

        else:
            self.show_real = False
            actions.append(action_default)
            actions.append(action_diff_abs)
            actions.append(action_diff_rel)            
            
            action_default.toggle() 
            action_diff_abs.toggle()
            action_diff_rel.toggle()
            
        add_actions(self.select_menu, actions)

        self.do_not_update = False
        self.update_view()
        self.calculated()
        QApplication.restoreOverrideCursor()
        
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True
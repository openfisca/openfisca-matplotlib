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


from src.gui.qt.QtGui import (QWidget, QVBoxLayout, QSizePolicy, QMenu,
                         QGroupBox, QFileDialog, QMessageBox)
from src.gui.qt.QtCore import SIGNAL, Qt

from src.gui.config import get_icon

from src.gui.qthelpers import OfSs, DataFrameViewWidget
from src.gui.utils.qthelpers import create_action, add_actions

from src.lib.utils import of_import

from src import SRC_PATH
from src.lib.simulation import SurveySimulation

from src.plugins import OpenfiscaPluginWidget, PluginConfigPage
from src.gui.baseconfig import get_translation
_ = get_translation("src")

    
class Aggregates(object):
    def __init__(self):
        super(Aggregates, self).__init__()

        self.simulation = None
        self.data = None
        self.data_default = None
        self.totals_df = None
        self.set_header_labels()
        self.show_default = False
        self.show_real = True
        self.show_diff = True
        self.varlist = None
        self.filter_by = None

    def set_var_list(self, var_list):
        """
        Set list of variables to be aggregated 
        """
        self.varlist = var_list

    def set_filter_by(self, varname):
        """
        Set the variable to filter by the amounts and beneficiaries that are
        to be taken into account 
        """
        self.filter_by = varname

    def set_default_var_list(self):
        """
        Set list of variables to be aggregated
        """
        country = self.simulation.country
        AGGREGATES_DEFAULT_VARS = of_import("","AGGREGATES_DEFAULT_VARS", country)
        self.varlist = AGGREGATES_DEFAULT_VARS
        
    def set_default_filter_by_list(self):
        """
        Import country specific default filter by variables list
        """
        country = self.simulation.country
        FILTERING_VARS = of_import("","FILTERING_VARS", country)
        self.filter_by_var_list = FILTERING_VARS
    
    def set_default_filter_by(self):
        """
        Set country specific default filter by variable
        """
        self.set_default_filter_by_list()
        varname = self.filter_by_var_list[0]
        self.set_filter_by(varname)
        
    def set_header_labels(self):
        '''
        Sets headers labels
        '''        
        labels = dict()
        labels['var']    = u"Mesure"
        labels['entity'] = u"Entité"
        labels['dep']    = u"Dépenses \n(millions d'€)" 
        labels['benef']  = u"Bénéficiaires \n(milliers)"
        labels['dep_default']   = u"Dépenses initiales \n(millions d'€)"
        labels['benef_default'] = u"Bénéficiaires \ninitiaux \n(milliers)"
        labels['dep_real']      = u"Dépenses \nréelles \n(millions d'€)"
        labels['benef_real']    = u"Bénéficiaires \nréels \n(milliers)"
        labels['dep_diff_abs']      = u"Diff. absolue \nDépenses \n(millions d'€) "
        labels['benef_diff_abs']    = u"Diff absolue \nBénéficiaires \n(milliers)"
        labels['dep_diff_rel']      = u"Diff. relative \nDépenses"
        labels['benef_diff_rel']    = u"Diff. relative \nBénéficiaires"
        self.labels = labels
        self.labels_ordered_list = ['var', 'entity', 'dep', 'benef', 'dep_default', 'benef_default',
                                    'dep_real', 'benef_real', 'dep_diff_abs', 'benef_diff_abs',
                                    'dep_diff_rel', 'benef_diff_rel']
        
    def set_simulation(self, simulation):
        
        if isinstance(simulation, SurveySimulation):
            self.simulation = simulation
        else:
            raise Exception('Aggregates:  %s should be an instance of %s class'  %(simulation, SurveySimulation))
        self.set_default_var_list()
        self.set_default_filter_by()

    def compute(self):
        """
        Compute the whole table
        """
        filter_by = self.filter_by
#        try:
        self.compute_aggregates(filter_by)
#        except Exception, e:
#            raise Exception("Cannot compute aggregates.\n compute_aggregates returned error '%s'" % e)
        self.load_amounts_from_file()
        self.compute_real()
        self.compute_diff()


    def compute_aggregates(self, filter_by = None):
        """
        Compute aggregate amounts
        """
        if self.simulation.output_table is None:
            raise Exception("No output_table found for the current survey_simulation")
        
        V  = []    
        M = {'data': [], 'default': []}
        B = {'data': [], 'default': []}
        U = []

        M_label = {'data': self.labels['dep'], 
                   'default': self.labels['dep_default']}
        B_label = {'data': self.labels['benef'], 
                   'default': self.labels['benef_default']}

        simulation = self.simulation
        for var in self.varlist:
            # amounts and beneficiaries from current data and default data if exists
            montant_benef = self.get_aggregate(var, filter_by)
            V.append(simulation.var2label[var])        
            try:
                varcol  = simulation.get_col(var)
                entity = varcol.entity
            except:
                entity = 'NA'
                 
            U.append(entity)
            for dataname in montant_benef:
                M[dataname].append( montant_benef[dataname][0] )
                B[dataname].append( montant_benef[dataname][1] )
        
        # build items list
        items = [(self.labels['var'], V)]

        for dataname in M:
            if M[dataname]:
                items.append( (M_label[dataname], M[dataname]))
                items.append(  (B_label[dataname], B[dataname]) )

        items.append( (self.labels['entity'], U) )        
        aggr_frame = DataFrame.from_items(items)
        
        self.aggr_frame = None
        for code in self.labels_ordered_list:
            try:
                col = aggr_frame[self.labels[code]]
                if self.aggr_frame is None:
                    self.aggr_frame = DataFrame(col)
                else:
                    self.aggr_frame = self.aggr_frame.join(col, how="outer")
            except:
                pass



    def get_aggregate(self, variable, filter_by=None):
        """
        Returns aggregate spending, and number of beneficiaries
        for the relevant entity level
        
        Parameters
        ----------
        variable : string
                   name of the variable aggregated according to its entity  
        """
        
        country = self.simulation.country
        WEIGHT = of_import("","WEIGHT", country)
        simulation = self.simulation
#        description = simulation.output_table.description
        
        def aggregate(var, filter_by):  # TODO: should be a method of Presta
            varcol  = simulation.get_col(var)
            entity = varcol.entity
            # amounts and beneficiaries from current data and default data if exists
            data, data_default = simulation.aggregated_by_entity(entity, [var], all_output_vars = False, force_sum = True)

            filter = 1        
            if filter_by is not None:
                data_filter, data_default_filter = simulation.aggregated_by_entity(entity, [filter_by], all_output_vars = False, force_sum = True)
                filter = data_filter[filter_by]
            datasets = {'data': data}
            m_b = {}
            weight = data[WEIGHT]*filter
            if data_default is not None:
                datasets['default'] = data_default
        
            for name, data in datasets.iteritems():
                montants = data[var]
                beneficiaires = data[var].values != 0
                from numpy import nan
                try:
                    amount = int(round(sum(montants*weight)/10**6))
                except:
                    amount = nan
                try:
                    benef = int(round(sum(beneficiaires*weight)/10**3))
                except:
                    benef = nan
                    
                m_b[name] = [amount, benef]
            
            return m_b
        
        return aggregate(variable, filter_by)
        

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
        self.aggr_frame[self.labels['dep_real']] = A
        self.aggr_frame[self.labels['benef_real']] = B

        
    def compute_diff(self):
        '''
        Computes and adds relative differences
        '''

        dep   = self.aggr_frame[self.labels['dep']]
        benef = self.aggr_frame[self.labels['benef']]
        
        if self.show_default:
            ref_dep_label, ref_benef_label = self.labels['dep_default'], self.labels['benef_default']
            if ref_dep_label not in self.aggr_frame:
                return
        elif self.show_real:
            ref_dep_label, ref_benef_label = self.labels['dep_real'], self.labels['benef_real']
        else:
            return
        
        ref_dep = self.aggr_frame[ref_dep_label]   
        ref_benef = self.aggr_frame[ref_benef_label]
                    
        self.aggr_frame[self.labels['dep_diff_rel']]   = (dep-ref_dep)/abs(ref_dep)
        self.aggr_frame[self.labels['benef_diff_rel']] = (benef-ref_benef)/abs(ref_benef)
        self.aggr_frame[self.labels['dep_diff_abs']]   = (dep-ref_dep)
        self.aggr_frame[self.labels['benef_diff_abs']] = (benef-ref_benef)
        

        
    def load_amounts_from_file(self, filename = None, year = None):
        '''
        Loads totals from files
        '''
        from pandas import HDFStore
        if year is None:
            year     = self.simulation.datesim.year
        if filename is None:
            country = self.simulation.country

            data_dir = os.path.join(SRC_PATH, 'countries', country, 'data')


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
                
                # Deals with logt
                logt = 0
                for var in ['apl', 'alf', 'als']:
                    logt += self.totals_df.get_value(var, col)
                self.totals_df.set_value('logt', col,  logt)
               
                # Deals with rsa rmi
                rsa = 0
                for var in ['rmi', 'rsa']:
                    rsa += self.totals_df.get_value(var, col)
                self.totals_df.set_value('rsa', col, rsa)
                
 
                # Deals with irpp, csg, crds

                for var in ['irpp', 'csg', 'crds', 'cotsoc_noncontrib']:
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
                         u"Données d'enquêtes de l'année %s" %str(self.simulation.input_table.survey_year) ]
        return DataFrame(descr)
        
    
    def clear(self):
        self.data = None
        self.data_default = None
        self.totals_df = None
        
    def get_aggregates(self, variable):
        self.aggr_frame
        
        
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

        self.show_dep = self.get_option('show_dep')
        self.show_benef = self.get_option('show_benef')        
        self.show_real = self.get_option('show_real')
        self.show_diff = self.get_option('show_diff')
        self.show_diff_abs = self.get_option('show_diff_abs')
        self.show_diff_rel = self.get_option('show_diff_rel')
        self.show_default = self.get_option('show_default')
        
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


    def toggle_option(self, option, boolean):
        self.set_option(option, boolean)
        self.show_dep = boolean
        self.update_view()
        

        
    def update_view(self):
        '''
        Update aggregate amounts view
        '''
        if self.aggregates.aggr_frame is None:
            return
            
        cols = [self.aggregates.labels[code] for code in self.aggregates.labels_ordered_list]

        labels = self.aggregates.labels
        
        if not self.get_option('show_real'):
            cols.remove(labels['dep_real'])
            cols.remove(labels['benef_real'])

        if (not self.get_option('show_default')) or self.aggregates.simulation.reforme is False:
            cols.remove(labels['dep_default'])
            cols.remove(labels['benef_default'])

        remove_all_diffs =  not (self.aggregates.show_real or self.aggregates.show_default)
        if not remove_all_diffs:
            self.aggregates.compute_diff()
        
        if (not self.get_option('show_diff_abs')) or remove_all_diffs:

            cols.remove(labels['dep_diff_abs'])
            cols.remove(labels['benef_diff_abs'])    
        
        if (not self.get_option('show_diff_rel')) or remove_all_diffs: 
            cols.remove(labels['dep_diff_rel'])
            cols.remove(labels['benef_diff_rel'])
 
        if not self.get_option('show_dep'):
            for label in [labels['dep'], labels['dep_real'],
                          labels['dep_default'], labels['dep_diff_abs'],
                          labels['dep_diff_rel']]:

                if label in cols:
                    cols.remove(label)

        if not self.get_option('show_benef'):
            for label in [labels['benef'], labels['benef_real'], 
                          labels['benef_default'], labels['benef_diff_abs'],
                          labels['benef_diff_rel']]:

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
         
        
    def save_table(self, table_format = None, float_format = "%.2f"):
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
                    df.to_excel(writer, "aggregates", index= False, header= True, float_format = float_format)
                    descr = self.create_description()
                    descr.to_excel(writer, "description", index = False, header=False)
                    writer.save()
                elif table_format =="csv":
                    df.to_csv(writer, "aggregates", index= False, header = True, float_format = float_format)
                     
                
            except Exception, e:
                QMessageBox.critical(
                    self, "Error saving file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)

    #------ OpenfiscaPluginMixin API ---------------------------------------------

    def apply_plugin_settings(self, options):
        """
        Apply configuration file's plugin settings
        """
        show_options = ['show_default', 'show_real', 'show_diff_abs',
                        'show_diff_abs', 'show_diff_rel', 'show_dep', 'show_benef']
        
        for option in options:
            if option in show_options:
                self.toggle_option(option, self.get_option(option))

#        if option is
    
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
        raise NotImplementedError
    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.main.add_dockwidget(self)


    def refresh_plugin(self):
        '''
        Update aggregate output_table and refresh view
        '''
        
        simulation = self.main.survey_simulation
        self.starting_long_process(_("Refreshing aggregates table ..."))
        agg = Aggregates()
        agg.set_simulation(simulation)
        agg.compute()
        
        self.aggregates = agg
        self.survey_year = self.aggregates.simulation.input_table.survey_year
        self.description = self.aggregates.simulation.output_table.description

        self.select_menu = QMenu()
        action_dep = create_action(self, u"Dépenses", 
                                   toggled = lambda boolean: self.toggle_option('show_dep', boolean))
        action_benef = create_action(self, u"Bénéficiaires",
                                     toggled = lambda boolean: self.toggle_option('show_benef', boolean))
        action_real = create_action(self, u"Réel",
                                   toggled = lambda boolean: self.toggle_option('show_real', boolean))
        action_diff_abs = create_action(self, u"Diff. absolue",
                                       toggled = lambda boolean: self.toggle_option('show_diff_abs', boolean))
        action_diff_rel = create_action(self, u"Diff. relative ",
                                       toggled = lambda boolean: self.toggle_option('show_diff_rel', boolean))
        action_default = create_action(self, u"Référence",
                                       toggled = lambda boolean: self.toggle_option('show_default', boolean))
                
        actions = [action_dep, action_benef]        
        action_dep.toggle()
        action_benef.toggle()
                
        if self.aggregates.simulation.reforme is False:
            self.set_option('show_default', False) 
            if self.aggregates.totals_df is not None: # real available
                actions.append(action_real)
                actions.append(action_diff_abs)
                actions.append(action_diff_rel)
                action_real.toggle()
                action_diff_abs.toggle()
                action_diff_rel.toggle()
            else: 
                self.set_option('show_real', False)
                self.set_option('show_diff_abs', False)
                self.set_option('show_diff_rel', False)

        else:
            self.set_option('show_real', False)
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
        self.ending_long_process(_("Aggregates table updated"))
    
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True
    
    
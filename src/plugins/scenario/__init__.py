# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

from src.gui.qt.QtGui import QGroupBox, QVBoxLayout
from src.plugins import OpenfiscaPluginWidget, PluginConfigPage
from src.gui.baseconfig import get_translation
_ = get_translation('src')

class CompositionConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Composer")
        
    def setup_page(self):

        axis_group = QGroupBox(_("Axis"))

        xaxis_choices = [(u'Salaires', 'sal'),(u'Chômage', 'cho'), (u'Retraites', 'rst')]
        xaxis_combo = self.create_combobox('Axe des abscisses', xaxis_choices, 'xaxis')
        nmen_spinbox = self.create_spinbox(u'Nombre de ménages', '', 'nmen', min_ = 1, max_ = 10001, step = 100)
        minrev_spinbox = self.create_spinbox("Revenu minimal", 
                                             'euros', 'minrev', min_ = 0, max_ = 10000000, step = 1000)
        maxrev_spinbox = self.create_spinbox("Revenu maximum", 
                                             'euros', 'maxrev', min_ = 0, max_ = 10000000, step = 1000)
        
        #xaxis          
        layout = QVBoxLayout()

        layout.addWidget(xaxis_combo)
        layout.addWidget(minrev_spinbox)    
        layout.addWidget(maxrev_spinbox)
        layout.addWidget(nmen_spinbox)        
        axis_group.setLayout(layout)


        legend_group = QGroupBox(_("Legend"))

        legend_enable  = self.create_checkbox('Insert legend', 'graph/legend/enable')
        
        choices = [( _('upper right'), 1),
                   (_('upper left'), 2),
                   (_('lower left'), 3),
                   (_('lower right'), 4),
                   (_('right'), 5),
                   (_('center left'), 6),
                   (_('center right'), 7),
                   (_('lower center'), 8),
                   (_('upper center'), 9),
                   (_('center'), 10 )]
        legend_location = self.create_combobox( _('Legend location'), choices, 'graph/legend/location')
        
        # xaxis  
        
        layout = QVBoxLayout()
        layout.addWidget(legend_enable)
        layout.addWidget(legend_location)
        legend_group.setLayout(layout)


        export_group = QGroupBox(_("Export"))
        choices = [('cvs', 'csv'),
                   ('xls', 'xls'),]
        table_format = self.create_combobox(_('Table export format'), choices, 'table/format')
        
        # TODO: export format for figure  
        
        reform_group = QGroupBox(_("Reform"))
        reform = self.create_checkbox(_('Reform mode'), 'reform')
        layout = QVBoxLayout()
        layout.addWidget(reform)
        reform_group.setLayout(layout)

        
        vlayout = QVBoxLayout()
        vlayout.addWidget(axis_group)
        vlayout.addWidget(legend_group)
        vlayout.addWidget(table_format)
        vlayout.addWidget(reform_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)

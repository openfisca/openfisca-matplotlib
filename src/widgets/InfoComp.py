# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

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
from src.gui.qt.QtGui import (QDialog, QSizePolicy, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                         QComboBox, QCheckBox, QSpacerItem, QDialogButtonBox)
from src.gui.qt.QtCore import SIGNAL
from src.gui.qthelpers import OfSs
from src.gui.utils.qthelpers import get_icon


class InfoComp(QDialog):
    '''
    A dialog to give complementary information on the member of the household:
    - activity
    - invalidity status
    - shared custody for children
    '''
    def __init__(self, scenario, parent = None):
        super(InfoComp, self).__init__(parent)

        self.resize(300, 223)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setWindowTitle(u"Informations complémentaires")
        icon = get_icon(":/images/people.png")
        self.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(self)
        self.gridLayout = QGridLayout()
        self.gridLayout.setHorizontalSpacing(10)
        self.setStyleSheet(OfSs.bold_center)

        self.label_0 = QLabel(u'n°', self)
        self.gridLayout.addWidget(self.label_0, 0, 0, 1, 1)

        self.label_1 = QLabel(u'Activité', self)
        self.gridLayout.addWidget(self.label_1, 0, 1, 1, 1)
        
        self.label_2 = QLabel(u"Invalide", self)
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)

        self.label_3 = QLabel(u'Garde\nalternée', self)
        self.gridLayout.addWidget(self.label_3, 0, 3, 1, 1)

        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setColumnStretch(3, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel| QDialogButtonBox.Ok, parent = self)
        self.verticalLayout.addWidget(self.buttonBox)

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept);
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject);

        self.parent = parent
        self.scenario = scenario
        self.inv_list = []
        self.alt_list = []
        self.act_list = []
        for noi, vals in self.scenario.indiv.iteritems():
            self.gridLayout.addWidget(QLabel('%d' % (noi + 1), self), noi + 1, 0)
            
            # Acitivité
            cb_act = QComboBox(self)
            cb_act.addItems([u'Actif occupé', u'Chômeur', u'Étudiant, élève', u'Retraité', u'Autre inactif'])
            cb_act.setCurrentIndex(vals['activite'])
            self.act_list.append(cb_act)
            self.gridLayout.addWidget(cb_act, noi + 1, 1)

            # Invalide
            cb_inv = QCheckBox(self)
            cb_inv.setChecked(vals['inv'])
            layout1 = QHBoxLayout()
            layout1.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            layout1.addWidget(cb_inv)
            layout1.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))            
            self.inv_list.append(cb_inv)
            self.gridLayout.addLayout(layout1, noi + 1, 2)

            # Garde alternée
            cb_alt = QCheckBox(self)
            if vals['quifoy'][:3] != 'pac':
                vals['alt'] = 0
                cb_alt.setEnabled(False)
            cb_alt.setChecked(vals['alt'])
            layout2 = QHBoxLayout()
            layout2.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            layout2.addWidget(cb_alt)
            layout2.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            self.alt_list.append(cb_alt)
            self.gridLayout.addLayout(layout2, noi + 1, 3)

    def accept(self):
        for noi, vals in self.scenario.indiv.iteritems():
            vals['inv'] = self.inv_list[noi].checkState() >= 1
            vals['alt'] = self.alt_list[noi].checkState() >= 1
            vals['activite'] = self.act_list[noi].currentIndex()
        QDialog.accept(self)
            

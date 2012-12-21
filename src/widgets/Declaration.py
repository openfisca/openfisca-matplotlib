# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

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

from views import ui_declaration, ui_page01, ui_page02, ui_page03, ui_page04, ui_page05, ui_page06, ui_page07, ui_page08, ui_page_isf
from PyQt4.QtCore import Qt, SIGNAL, QSize
from PyQt4.QtGui import QWidget, QDialog, QCheckBox, QSpinBox, QLabel, QStackedWidget, QListWidgetItem
from core.qthelpers import OfSs    

class Declaration(QDialog, ui_declaration.Ui_Declaration):
    def __init__(self, parent, noi):
        super(Declaration, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet(OfSs.declaration_page_style)
        self.noidec = noi
        self.parent = parent
        self.scenario = parent.scenario


        self.pages_widget = QStackedWidget(self)
        self.connect(self.pages_widget, SIGNAL("currentChanged(int)"), self.current_page_changed)
        self.connect(self.contents_widget, SIGNAL("currentRowChanged(int)"), self.pages_widget.setCurrentIndex)
                
        self.scrollArea.setWidget(self.pages_widget)

        self.connect(self.next_btn, SIGNAL('clicked()'), self.next_page)
        self.connect(self.prev_btn, SIGNAL('clicked()'), self.prev_page)

        self.pages = [Page01(self),  Page02(self), Page03(self), Page04(self), 
                      Page05(self), Page06(self), Page07(self), PageIsf(self)]

        for widget in self.pages:
            self.add_page(widget)


        self.set_current_index(0)
        self.current_page_changed(0)

    def current_page_changed(self, index):
        nb = self.pages_widget.count() - 1
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        if index == nb:
            self.next_btn.setEnabled(False)
        if index == 0:
            self.prev_btn.setEnabled(False)            

    def next_page(self):
        idx = self.pages_widget.currentIndex()
        self.set_current_index(idx + 1)

    def prev_page(self):
        idx = self.pages_widget.currentIndex()
        self.set_current_index(idx - 1)

    def get_current_index(self):
        """Return current page index"""
        return self.contents_widget.currentRow()
        
    def set_current_index(self, index):
        """Set current page index"""
        self.contents_widget.setCurrentRow(index)
        self.pages_widget.setCurrentIndex(index)

    def accept(self):
        for page in self.pages:
            for key in page.__dict__:
                widget = getattr(page,key)
                if  isinstance(widget, QSpinBox):
                    var = str(widget.objectName())
                    val = widget.value()
                    page.updateFoyer(var, val)
                elif isinstance(widget, QCheckBox):
                    var = str(widget.objectName())
                    val = 1*(widget.checkState()>=1)
                    page.updateFoyer(var, val)
        QDialog.accept(self)

    def add_page(self, widget):
        self.pages_widget.addWidget(widget)
        item = QListWidgetItem(self.contents_widget)
        item.setText(widget.get_name())
        item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

class Page(QWidget):
    def __init__(self, parent):
        super(Page, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.scenario = parent.scenario
        self.noidec = parent.noidec            
        self._type = u'Page non spécifiée'
        
        self.restore_values()
        
    def get_name(self):
        return self._type

    def setupUi(self, base):
        raise NotImplementedError

    def restore_values(self):
        for key, val in self.scenario.declar[self.noidec].iteritems():
            if hasattr(self, key):
                widget = getattr(self, key)
                if  isinstance(widget, QCheckBox): widget.setChecked(val)
                elif isinstance(widget, QSpinBox):  widget.setValue(val)
        
    def updateFoyer(self, key, val):
        if key[0] =='_':
            qui = int(key[1])
            key = key[2:]
            indiv = self.scenario.indiv[qui]
            indiv.update({key:val})
        else:
            indiv = self.scenario.declar[self.noidec]
#            if not indiv.has_key(key) and val != 0:
            indiv.update({key:val})

class Page01(ui_page01.Ui_Page01, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Composition du foyer'
        self.declar = self.scenario.declar[self.noidec]
        statmarit =  self.scenario.indiv[self.noidec]['statmarit']
        listw = ((self.M, self.codeM, self.nomM),
                (self.C, self.codeC, self.nomC),
                (self.D, self.codeD, self.nomD),
                (self.V, self.codeV, self.nomV),
                (self.O, self.codeO, self.nomO))
        
        [widget.setEnabled(True)  for widget in listw[0] if statmarit in (1,5)]
        [widget.setEnabled(False) for widget in listw[1] if statmarit in (1,5)]
        [widget.setEnabled(False) for widget in listw[2] if statmarit in (1,5)]
        [widget.setEnabled(False) for widget in listw[3] if statmarit in (1,5)]
        [widget.setEnabled(True)  for widget in listw[4] if statmarit in (1,5)]

        [widget.setEnabled(False) for widget in listw[0] if statmarit in (2,3,4)]
        [widget.setEnabled(True)  for widget in listw[1] if statmarit in (2,3,4)]
        [widget.setEnabled(True)  for widget in listw[2] if statmarit in (2,3,4)]
        [widget.setEnabled(True)  for widget in listw[3] if statmarit in (2,3,4)]
        [widget.setEnabled(False) for widget in listw[4] if statmarit in (2,3,4)]

        if   statmarit == 1: self.M.click()
        elif statmarit == 2: self.C.click()
        elif statmarit == 3: self.D.click()
        elif statmarit == 4: self.V.click()
        elif statmarit == 5: self.O.click()
        self.connect(self.M, SIGNAL('clicked()'), self.setStatmarit)
        self.connect(self.C, SIGNAL('clicked()'), self.setStatmarit)
        self.connect(self.D, SIGNAL('clicked()'), self.setStatmarit)
        self.connect(self.V, SIGNAL('clicked()'), self.setStatmarit)
        self.connect(self.O, SIGNAL('clicked()'), self.setStatmarit)
        
    def setStatmarit(self):
        sender = self.sender()
        statut = str(sender.objectName()[:])
        if   statut == 'M':  i = 1
        elif statut == 'C':  i = 2
        elif statut == 'D':  i = 3
        elif statut == 'V':  i = 4
        elif statut == 'O':  i = 5
        for vals in self.scenario.indiv.itervalues():
            if vals['noidec'] == self.noidec:
                if vals['quifoy'] in ('vous', 'conj'):
                    vals['statmarit'] = i

    def updateFoyer(self, sender, value):
        pass

class Page02(ui_page02.Ui_Page02, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Situation du foyer'

class Page03(ui_page03.Ui_Page03, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self.n = 0

        for noi, indiv in self.scenario.indiv.iteritems():
            if indiv['noidec'] != self.noidec: continue
            self.addColumn(noi, indiv['quifoy'])
            for key, val in indiv.iteritems():
                widgetName = '_%d%s' % (noi,key)
                if hasattr(self, widgetName):
                    widget = getattr(self, widgetName)
                    if isinstance(widget,QCheckBox):
                        widget.setChecked(val)
                    elif isinstance(widget,QSpinBox):
                        widget.setValue(val)
            
        self._type = u'Revenus, salaires, pensions et rentes'
                
    def addColumn(self, noi, quifoy):
        codes = [['sali',1], 
                 ['choi',2], 
                 ['fra',3], 
                 ['cho_ld',4], 
                 ['hsup',5],
                 ['ppe_tp_sa',7], 
                 ['ppe_du_sa',8],
                 ['rsti', 10],
                 ['alr',11]]
        if quifoy == 'vous': pos = 2
        elif quifoy == 'conj': pos = 4
        elif quifoy[:3] == 'pac': pos = 4+2*int(quifoy[3])
        self.gridLayout.addWidget(QLabel(quifoy, self), 0, pos, 1, 2)
        
        for code, row in codes:
            name = '_%d%s' % (noi, code)
            if code in ('cho_ld', 'ppe_tp_sa'):
                widget = self.addCheckBox(name)
                setattr(self, name, widget)
                self.gridLayout.addWidget(widget, row, pos+1, 1, 1)
                self.gridLayout.addWidget(QLabel('cochez', self), row, pos, 1, 1)
            else:    
                widget = self.addSpinBox(name)
                setattr(self, name, widget)
                self.gridLayout.addWidget(widget, row, pos, 1, 2)
        
    def addSpinBox(self, name):
        sb = QSpinBox(self)
        sb.setEnabled(True)
        sb.setMinimumSize(QSize(60, 20))
        sb.setMaximumSize(QSize(60, 20))
        sb.setWrapping(False)
        sb.setFrame(True)
        sb.setButtonSymbols(QSpinBox.NoButtons)
        sb.setAccelerated(True)
        sb.setCorrectionMode(QSpinBox.CorrectToPreviousValue)
        sb.setKeyboardTracking(True)
        sb.setMinimum(0)
        sb.setMaximum(99999999)
        sb.setSingleStep(1000)
        sb.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        sb.setProperty("value", 0)
        sb.setObjectName(name)
        return sb

    def addCheckBox(self, name):
        cb = QCheckBox(self)
        cb.setText("")
        cb.setObjectName(name)
        return cb

class Page04(ui_page04.Ui_Page04, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Revenus des valeurs et capitaux mobiliers'

class Page05(ui_page05.Ui_Page05, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Plus values et revenus fonciers'

class Page06(ui_page06.Ui_Page06, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Charges déductibles'

class Page07(ui_page07.Ui_Page07, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u"Réduction et crédit d'impôt"
         
class Page08(ui_page08.Ui_Page08, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Divers'

class PageIsf(ui_page_isf.Ui_Page_isf, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'ISF'

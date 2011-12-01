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

from views import ui_declaration, ui_page01, ui_page02A, ui_page03A, ui_page03B, ui_page03C, ui_page04A, ui_page04B, ui_page04C
from PyQt4.QtCore import QAbstractListModel, Qt, QVariant, SIGNAL, QSize
from PyQt4.QtGui import QWidget, QVBoxLayout, QDialog, QCheckBox, QSpinBox, QLabel
    
class Declaration(QDialog, ui_declaration.Ui_Declaration):
    def __init__(self, parent, noi):
        super(Declaration, self).__init__(parent)
        self.setupUi(self)
        self.noidec = noi
        self.parent = parent
        self.scenario = parent.scenario

        self.pagesSlideShow = PagesSlideShow(self)
        self.scrollArea.setWidget(self.pagesSlideShow)

        self.pagesModel = PagesModel(self.pagesSlideShow.pages)
        self.navigationView.setModel(self.pagesModel)
        self.selectionModel = self.navigationView.selectionModel()
        self._nbpages = len(self.pagesSlideShow.pages)
        
        for page in self.pagesSlideShow.pages:
            page.setVisible(False)

        self._currentPage = 0
        self.getPage(self._currentPage)

        self.connect(self.nextButton,SIGNAL('clicked()'),self.nextPage)
        self.connect(self.prevButton,SIGNAL('clicked()'),self.prevPage)
        self.connect(self.selectionModel,SIGNAL('currentChanged(QModelIndex, QModelIndex)'), self.getSelection)

    def getSelection(self, startIndex, endIndex):
        self.getPage(startIndex.row())
    
    def getPage(self,pageIndex = 0):
        self.pagesSlideShow.pages[self._currentPage].setVisible(False)
        self._currentPage = pageIndex
        self.pagesSlideShow.pages[self._currentPage].setVisible(True)
        self.prevButton.setEnabled(True)
        self.nextButton.setEnabled(True)
        if self._currentPage == 0:
            self.prevButton.setEnabled(False)
        elif self._currentPage >= self._nbpages -1:
            self.nextButton.setEnabled(False)
        self.selectionModel.setCurrentIndex(self.pagesModel.index(self._currentPage),self.selectionModel.ClearAndSelect )
        
    def nextPage(self):
        self.getPage(self._currentPage +1 )
    
    def prevPage(self):
        self.getPage(self._currentPage -1)

    def accept(self):
        for page in self.pagesSlideShow.pages:
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

class PagesSlideShow(QWidget):
    def __init__(self, parent):
        super(PagesSlideShow, self).__init__(parent)

        self.parent = parent
        self.scenario = parent.scenario
        self.noidec = parent.noidec

        self.pages = [Page01(self),  Page02A(self), Page03A(self), Page03B(self), 
                      Page03C(self), Page04A(self), Page04B(self)]
        
        self.declarationLayout = QVBoxLayout(self)
        self.setLayout(self.declarationLayout)
        
        for page in self.pages:
            self.declarationLayout.addWidget(page)

class Page(QWidget):
    def __init__(self, parent):
        super(Page, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.scenario = parent.scenario
        self.noidec = parent.noidec            
        self._type = u'Page non spécifiée'
        
        self.restore_values()

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

class Page02A(ui_page02A.Ui_Page02A, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Situation du foyer'

class Page03A(ui_page03A.Ui_Page03A, Page):
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

class Page03B(ui_page03B.Ui_Page03B, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Revenus des valeurs et capitaux mobiliers'

class Page03C(ui_page03C.Ui_Page03C, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Plus values et revenus fonciers'

class Page04A(ui_page04A.Ui_Page04A, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Charges déductibles'

class Page04B(ui_page04B.Ui_Page04B, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u"Réduction et crédit d'impôt"
         
class Page04C(ui_page04C.Ui_Page04C, Page):
    def __init__(self, parent):
        Page.__init__(self, parent)
        self._type = u'Divers'

class PagesModel(QAbstractListModel):
    def __init__(self, pages = [], parent = None):
        super(PagesModel,self).__init__(parent)
        self.__pages = pages

    def headerData(self, section, orientation, role):        
        return QVariant()

    def rowCount(self, parent):
        return len(self.__pages)

    def data(self, index, role):                
        if role == Qt.DisplayRole:            
            value = self.__pages[index.row()]            
            return value._type

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        

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

from PyQt4.QtGui import (QDockWidget, QDialog, QLabel, QDateEdit, QComboBox, QCheckBox, 
                         QPushButton, QApplication, QFileDialog, QMessageBox,
                         QSpacerItem, QHBoxLayout, QSizePolicy)
from PyQt4.QtCore import QObject, SIGNAL, SLOT, QDate, Qt
from views.ui_composition import Ui_Menage
from views.ui_logement import Ui_Logement
from views.ui_infocomp import Ui_InfoComp
from Declaration import Declaration
from datetime import date
import pickle

class S:
    name = 0
    birth = 1
    decnum = 2
    decpos = 3
    decbtn = 4
    famnum = 5
    fampos = 6

class ScenarioWidget(QDockWidget, Ui_Menage):
    def __init__(self, scenario, parent = None):
        super(ScenarioWidget, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.scenario = scenario

        self.connect(self.open_btn, SIGNAL('clicked()'), self.openScenario)
        self.connect(self.save_btn, SIGNAL('clicked()'), self.saveScenario)
        self.connect(self.add_btn, SIGNAL('clicked()'), self.addPerson)
        self.connect(self.rmv_btn, SIGNAL('clicked()'), self.rmvPerson)
        self.connect(self.lgt_btn, SIGNAL('clicked()'), self.openLogement)
        self.connect(self.inf_btn, SIGNAL('clicked()'), self.openInfoComp)
        self.connect(self, SIGNAL('compoChanged()'), self.changed)

        self._listPerson = []
        self.addPref()
        self.rmv_btn.setEnabled(False)
        self.emit(SIGNAL("ok()"))

    def changed(self):
        self.disconnectAll()
        self.scenario.genNbEnf()
        self.populate()
        self.emit(SIGNAL('changed()'))
        self.connectAll()
        
    def nbRow(self):
        return self.scenario.nbIndiv()

    def populate(self):
        self.populateBirth()
        self.populateQuifoyCombo()
        self.populateFoyerCombo()
        self.populateQuifamCombo()
        self.populateFamilleCombo()

    def populateBirth(self):
        for noi, vals in self.scenario.indiv.iteritems():
            birth = QDate(vals['birth'])
            self._listPerson[noi][S.birth].setDate(birth)
        
    def populateFoyerCombo(self):
        declarKeys = self.scenario.declar.keys()
        for noi, vals in self.scenario.indiv.iteritems():
            noidec = vals['noidec']
            box = self._listPerson[noi][S.decnum]
            box.clear()
            button = self._listPerson[noi][S.decbtn]
            button.setText('Foyer %d' % (noidec+1))
            if vals['quifoy'] == 'vous':
                box.addItems(['%d' % (noidec+1)])
                button.setEnabled(True)
            else :
                box.addItems(['%d' % (k+1) for k in declarKeys])
                button.setEnabled(False)
                box.setCurrentIndex(declarKeys.index(noidec))

    def populateQuifoyCombo(self):
        for noi, vals in self.scenario.indiv.iteritems():
            quifoy = vals['quifoy']
            # retrieve the foyer combobox of individu number noi
            box = self._listPerson[noi][S.decpos]
            # set the combobox to 'vous' 'conj' or 'pac'
            if   quifoy == 'vous': box.setCurrentIndex(0)
            elif quifoy == 'conj': box.setCurrentIndex(1)
            elif quifoy[:3] == 'pac': box.setCurrentIndex(2)

    def populateFamilleCombo(self):
        familleKeys = self.scenario.famille.keys()
        for noi, vals in self.scenario.indiv.iteritems():
            noichef = vals['noichef']
            box = self._listPerson[noi][S.famnum]
            box.clear()
            if vals['quifam'] == 'parent 1':
                box.addItems(['%d' % (noichef+1)])
            else :
                box.addItems(['%d' % (k+1) for k in familleKeys])
                box.setCurrentIndex(familleKeys.index(noichef))

    def populateQuifamCombo(self):
        for noi, vals in self.scenario.indiv.iteritems():
            quifam = vals['quifam']
            # retrieve the foyer combobox of individu number noi
            box = self._listPerson[noi][S.fampos]
            # set the combobox to 'parent 1' 'parent 2' or 'enfant'
            if   quifam == 'chef': box.setCurrentIndex(0)
            elif quifam == 'part': box.setCurrentIndex(1)
            elif quifam[:3] == 'enf': box.setCurrentIndex(2)

    def birthChanged(self, date):
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.indiv[senderNoi].update({'birth': date.toPyDate()})
        self.emit(SIGNAL('compoChanged()'))

    def foyerChanged(self):
        sender = self.sender()
        noi = int(sender.objectName()[3])
        newfoyer = int(sender.currentText()[-1])-1
        self.scenario.modify(noi, newFoyer = newfoyer)
        self.emit(SIGNAL('compoChanged()'))

    def quifoyChanged(self, newQuifoy):
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.modify(senderNoi, newQuifoy = newQuifoy)
        self.emit(SIGNAL('compoChanged()'))

    def familleChanged(self):
        sender = self.sender()
        noi = int(sender.objectName()[3])
        newfamille = int(sender.currentText()[-1])-1
        self.scenario.modifyFam(noi, newFamille = newfamille)
        self.emit(SIGNAL('compoChanged()'))

    def quifamChanged(self, newFam):
        if newFam == 'parent 1' : qui = 'chef'
        elif newFam == 'parent 2' : qui = 'part'
        elif newFam == 'enfant' : qui = 'enf'
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.modifyFam(senderNoi, newQuifam = qui)
        self.emit(SIGNAL('compoChanged()'))
        

    def addPref(self):
        noi = 0
        self._listPerson.append([QLabel('%d' % (noi+1), self),
                                 QDateEdit(self),
                                 QComboBox(self),
                                 QComboBox(self),
                                 QPushButton(self),
                                 QComboBox(self),
                                 QComboBox(self)])

        temp = self._listPerson[0]

        temp[S.birth].setDisplayFormat(QApplication.translate("Page01", "dd MMM yyyy", None, QApplication.UnicodeUTF8))
        temp[S.birth].setObjectName('Bir%d' % noi)
        temp[S.birth].setCurrentSection(QDateEdit.YearSection)

        temp[S.decpos].setObjectName('Dec%d' % noi)
        temp[S.decpos].addItems(['vous'])
        temp[S.decpos].setEnabled(False)

        temp[S.decnum].setObjectName('Foy%d' % noi)
        temp[S.decnum].setEnabled(False)

        temp[S.fampos].addItems(['parent 1'])            
        temp[S.fampos].setObjectName('Fam%d' % noi)
        temp[S.fampos].setEnabled(False)

        temp[S.famnum].setObjectName('Fam%d' % noi)
        temp[S.famnum].setEnabled(False)

        temp[S.decbtn].setObjectName('But%d' % noi)

        for i in xrange(7):
            self.gridLayout.addWidget(temp[i], noi + 2, i)
            self.gridLayout.setAlignment(temp[i], Qt.AlignCenter)

        self.emit(SIGNAL('compoChanged()'))
                
    def addPerson(self):
        noi = self.nbRow()
        self.addRow()
        if noi == 1: self.scenario.addIndiv(noi, birth = date(1975,1,1), quifoy = 'conj', quifam = 'part')
        else:        self.scenario.addIndiv(noi, birth = date(2000,1,1), quifoy = 'pac' , quifam = 'enf')
        self.emit(SIGNAL('compoChanged()'))
            
    def addRow(self):
        noi = len(self._listPerson)
        self._listPerson.append([QLabel('%d' % (noi+1), self),
                                 QDateEdit(self),
                                 QComboBox(self),
                                 QComboBox(self),
                                 QPushButton(self),
                                 QComboBox(self),
                                 QComboBox(self)])
        temp = self._listPerson[-1]

        temp[S.birth].setDisplayFormat(QApplication.translate("Page01", "dd MMM yyyy", None, QApplication.UnicodeUTF8))
        temp[S.birth].setObjectName('Bir%d' % noi)
        temp[S.birth].setCurrentSection(QDateEdit.YearSection)

        temp[S.decpos].setObjectName('Dec%d' % noi)
        temp[S.decpos].addItems(['vous', 'conj', 'pac'])

        temp[S.decnum].setObjectName('Foy%d' % noi)

        temp[S.fampos].setObjectName('Fam%d' % noi)
        temp[S.fampos].addItems(['parent 1', 'parent 2', 'enfant'])

        temp[S.famnum].setObjectName('Fam%d' % noi)

        temp[S.decbtn].setObjectName('But%d' % noi)
        
        for i in xrange(7):
            self.gridLayout.addWidget(temp[i], noi +2, i)
            self.gridLayout.setAlignment(temp[i], Qt.AlignCenter)


        self.rmv_btn.setEnabled(True)
        if len(self.scenario.indiv) == 9:
            self.add_btn.setEnabled(False)

    def rmvPerson(self, noi = None):
        if noi == None: noi = self.nbRow() - 1
        self.scenario.rmvIndiv(noi)
        self.rmvRow()
        self.add_btn.setEnabled(True)

        self.emit(SIGNAL('compoChanged()'))

    def rmvRow(self):
        '''
        Enlève le dernier individu et l'efface dans le foyer
        '''
        toDel = self._listPerson.pop()
        for widget in toDel:
            widget.setParent(None)
        if len(self.scenario.indiv) == 1: self.rmv_btn.setEnabled(False)

    def openDeclaration(self):
        noi = int(self.sender().objectName()[3])
        self.scenario.genNbEnf()
        msg = self.scenario.check_consistency()
        if msg:
            QMessageBox.critical(self, u"Ménage non valide",
                                 msg, 
                                 QMessageBox.Ok, QMessageBox.NoButton)
            return False
        self._declaration = Declaration(self, noi)
        self._declaration.exec_()
        self.emit(SIGNAL('compoChanged()'))

    def openLogement(self):
        self._logement = Logement(self.scenario, self)
        self._logement.exec_()
        self.emit(SIGNAL('compoChanged()'))

    def openInfoComp(self):
        self._infocomp = InfoComp(self.scenario, self)
        self._infocomp.exec_()
        self.emit(SIGNAL('compoChanged()'))
        
    def disconnectAll(self):
        for person in self._listPerson:
            QObject.disconnect(person[S.birth],  SIGNAL('dateChanged(QDate)'), self.birthChanged)
            QObject.disconnect(person[S.decpos], SIGNAL('currentIndexChanged(QString)'), self.quifoyChanged)
            QObject.disconnect(person[S.decnum], SIGNAL('currentIndexChanged(int)'), self.foyerChanged)
            QObject.disconnect(person[S.fampos], SIGNAL('currentIndexChanged(QString)'), self.quifamChanged)
            QObject.disconnect(person[S.famnum], SIGNAL('currentIndexChanged(int)'), self.familleChanged)
            QObject.disconnect(person[S.decbtn], SIGNAL('clicked()'), self.openDeclaration)
            
    def connectAll(self):
        for person in self._listPerson:
            QObject.connect(person[S.birth],  SIGNAL('dateChanged(QDate)'), self.birthChanged)
            QObject.connect(person[S.decpos], SIGNAL('currentIndexChanged(QString)'), self.quifoyChanged)
            QObject.connect(person[S.decnum], SIGNAL('currentIndexChanged(int)'), self.foyerChanged)
            QObject.connect(person[S.fampos], SIGNAL('currentIndexChanged(QString)'), self.quifamChanged)
            QObject.connect(person[S.famnum], SIGNAL('currentIndexChanged(int)'), self.familleChanged)
            QObject.connect(person[S.decbtn], SIGNAL('clicked()'), self.openDeclaration)

    def openScenario(self):
        fileName = QFileDialog.getOpenFileName(self,
                                               u"Ouvrir un cas type", 
                                               "castypes/", 
                                               u"Cas type OpenFisca (*.ofct)")
        if not fileName == '':
            n = len(self.scenario.indiv)
            try:
                self.scenario.openFile(fileName)
                while n < self.nbRow():
                    self.addRow()
                    n += 1
                while n > self.nbRow(): 
                    self.rmvRow()
                    n -= 1
                self.emit(SIGNAL('compoChanged()'))
                self.emit(SIGNAL("ok()"))
            except Exception, e:
                QMessageBox.critical(
                    self, "Erreur", u"Erreur lors de l'ouverture du fichier : le fichier n'est pas reconnu",
                    QMessageBox.Ok, QMessageBox.NoButton)

        
    def saveScenario(self):
        fileName = QFileDialog.getSaveFileName(self,
                                               u"Sauver un cas type", 
                                               "castypes/sans-titre", 
                                               u"Cas type OpenFisca (*.ofct)")
        if not fileName == '':
            self.scenario.saveFile(fileName)

class Logement(QDialog, Ui_Logement):
    def __init__(self, scenario, parent = None):
        super(Logement, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.scenario = scenario
        self.spinCP.setValue(scenario.menage[0]['code_postal'])
        self.spinLoyer.setValue(scenario.menage[0]['loyer'])
        self.comboSo.setCurrentIndex(scenario.menage[0]['so']-1)
                        
        code_file = open('data/code_apl', 'rb')
        code_dict = pickle.load(code_file)
        code_file.close()

        def update_ville(code):        
            try:
                commune = code_dict[str(code)]
            except:
                commune = ("Ce code postal n'est pas reconnu", '2')
                
            self.commune.setText(commune[0])
            self.spinZone.setValue(int(commune[1]))

        update_ville(self.spinCP.value())

        self.connect(self.spinCP, SIGNAL('valueChanged(int)'), update_ville)
        
        def so_changed(value):
            if value in (0,1):
                self.spinLoyer.setValue(0)
                self.spinLoyer.setEnabled(False)
            else:
                self.spinLoyer.setValue(500)
                self.spinLoyer.setEnabled(True)
                
        self.connect(self.comboSo, SIGNAL('currentIndexChanged(int)'), so_changed)
        self.connect(self.bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(self.bbox, SIGNAL("rejected()"), SLOT("reject()"))
        
    def accept(self):
        self.scenario.menage[0].update({'loyer': int(self.spinLoyer.value()),
                                        'so': int(self.comboSo.currentIndex()+1),
                                        'zone_apl': int(self.spinZone.value()),
                                        'code_postal': int(self.spinCP.value())})
        QDialog.accept(self)


class InfoComp(QDialog, Ui_InfoComp):
    def __init__(self, scenario, parent = None):
        super(InfoComp, self).__init__(parent)
        self.setupUi(self)
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
            

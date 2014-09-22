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
from __future__ import division


import os
import numpy as np
import xml

from openfisca_core import decompositions, decompositionsxml
from openfisca_web_api import conv


class OutNode(object):
    def __init__(self, code, desc, shortname = '', vals = 0, color = (0, 0, 0), typevar = 0, parent = None):
        self.parent = parent
        self.children = []
        self.code = code
        self.desc = desc
        self.color = color
        self.visible = 0
        self.typevar = typevar
        self._vals = vals
        self._taille = 0
        if shortname:
            self.shortname = shortname
        else:
            self.shortname = code

    def addChild(self, child):
        self.children.append(child)
        if child.color == (0, 0, 0):
            child.color = self.color
        child.setParent(self)

    def setParent(self, parent):
        self.parent = parent

    def child(self, row):
        return(self.children[row])

    def childCount(self):
        return len(self.children)

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

    def setLeavesVisible(self):
        for child in self.children:
            child.setLeavesVisible()
        if (self.children and (self.code != 'revdisp')) or (self.code == 'nivvie'):
            self.visible = 0
        else:
            self.visible = 1

    def partiallychecked(self):
        if self.children:
            a = True
            for child in self.children:
                a = a and (child.partiallychecked() or child.visible)
            return a
        return False

    def hideAll(self):
        if self.code == 'revdisp':
            self.visible = 1
        else:
            self.visible = 0
        for child in self.children:
            child.hideAll()

    def setHidden(self, changeParent = True):
        # les siblings doivent être dans le même
        if self.partiallychecked():
            self.visible = 0
            return
        for sibling in self.parent.children:
            sibling.visible = 0
            for child in sibling.children:
                child.setHidden(False)
        if changeParent:
            self.parent.visible = 1

    def setVisible(self, changeSelf = True, changeParent = True):
        if changeSelf:
            self.visible = 1
        if self.parent is not None:
            for sibling in self.parent.children:
                if not (sibling.partiallychecked() or sibling.visible == 1):
                    sibling.visible = 1
            if changeParent:
                self.parent.setVisible(changeSelf = False)

    def getVals(self):
        return self._vals

    def setVals(self, vals):
        dif = vals - self._vals
        self._vals = vals
        self._taille = len(vals)
        if self.parent:
            self.parent.setVals(self.parent.vals + dif)

    vals = property(getVals, setVals)

    def __getitem__(self, key):
        if self.code == key:
            return self
        for child in self.children:
            val = child[key]
            if not val is None:
                return val

    def log(self, tabLevel=-1):
        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"

        output += "|------" + self.code + "\n"

        for child in self.children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    def __repr__(self):
        return self.log()

    def difference(self, other):
        self.vals -= other.vals
        for child in self.children:
            child.difference(other[child.code])

    def __iter__(self):
        return self.inorder()

    def inorder(self):
        for child in self.children:
            for x in child.inorder():
                yield x
        yield self

    @classmethod
    def create_from_scenario_decomposition_json(cls, scenario, decomposiiton_json, trace = False):
        simulation = scenario.new_simulation()
        tax_benefit_system = scenario.tax_benefit_system
        # TODO: handle properly default decomposition
        if decomposiiton_json is None:
            decomposition_tree = xml.etree.ElementTree.parse(
                os.path.join(
                    tax_benefit_system.DECOMP_DIR,
                    "decomp.xml"
                    )
                )
            decomposition_xml_json = conv.check(decompositionsxml.xml_decomposition_to_json)(
                decomposition_tree.getroot()
                )
            decomposition_xml_json = conv.check(decompositionsxml.make_validate_node_xml_json(tax_benefit_system))(
                decomposition_xml_json)
            decomposition_json = decompositionsxml.transform_node_xml_json_to_json(decomposition_xml_json)

        self = cls('root', 'root')
        # Compute for all decomposition nodes

        for node in decompositions.iter_decomposition_nodes(decomposition_json, children_first = True):
            children = node.get('children')
            if children:
                node['values'] = map(lambda *l: sum(l), *(
                    child['values']
                    for child in children
                    ))
            else:
                node['values'] = values = []
                holder = simulation.compute(node['code'])
                column = holder.column
                values.extend(
                    column.transform_value_to_json(value)
                    for value in holder.new_test_case_array().tolist()
                    )

        root_node = decomposition_json

        def convert_to_out_node(out_node, node):
            out_node.code = node['code']
            out_node.desc = node['name']
            if 'color' in node:
                out_node.cols = node['color']
            else:
                out_node.cols = [0, 0, 0]
            out_node.short = node['short_name']
            out_node.typv = 0
            if 'type' in node:
                out_node.typv = node['type']
            out_node.setVals(np.array(node['values']))

            if node.get('children'):
                for child in node.get('children'):
                    code = child['code']
                    desc = child['name']
                    if 'color' in child:
                        cols = child['color']
                    else:
                        cols = [0, 0, 0]
                    short = child['short_name']
                    typv = 0
                    if 'type' in child:
                        typv = child['type']
                    child_out_node = OutNode(code, desc, color = cols, typevar = typv, shortname = short)
                    out_node.addChild(child_out_node)
                    convert_to_out_node(child_out_node, child)
            else:
                if node['code'] in tax_benefit_system.column_by_name:
                    return
                else:
                    raise Exception('%s is not a variable of the tax_benefit_system' % tree.code)


        convert_to_out_node(self, root_node)
        return self


if __name__ == '__main__':
    import openfisca_france
    import datetime
    year = 2013
    TaxBenefitSystem = openfisca_france.init_country()
    tax_benefit_system = TaxBenefitSystem()
    scenario = tax_benefit_system.new_scenario().init_single_entity(
        parent1 = dict(
            birth = datetime.date(year - 40, 1, 1),
            sali = 50000),
        year = year,
        )
    tree = OutNode.create_from_scenario_decomposition_json(scenario, decomposiiton_json = None)
    print tree




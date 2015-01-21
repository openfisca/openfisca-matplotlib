# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division


import os

from openfisca_core.decompositions import get_decomposition_json
import openfisca_france


TaxBenefitSystem = openfisca_france.init_country()
tax_benefit_system = TaxBenefitSystem()


from openfisca_matplotlib.tests.test_graphs import create_simulation
from openfisca_matplotlib.dataframes import data_frame_from_decomposition_json


def test():
    reform_simulation, reference_simulation = create_simulation()
    data_frame = data_frame_from_decomposition_json(
        reform_simulation,
        decomposition_json = None,
        reference_simulation = reference_simulation,
        )
    return data_frame


def test_bareme():
    reform_simulation, reference_simulation = create_simulation(bareme = True)
    data_frame = data_frame_from_decomposition_json(
        reform_simulation,
        decomposition_json = None,
        reference_simulation = reference_simulation,
        )
    return data_frame


def test_remove_null():
    reform_simulation, reference_simulation = create_simulation()
    data_frame = data_frame_from_decomposition_json(
        reform_simulation,
        decomposition_json = None,
        reference_simulation = reference_simulation,
        remove_null = True)
    return data_frame


def test_fiche_de_paie():
    reform_simulation, reference_simulation = create_simulation()
    xml_file_path = os.path.join(
        tax_benefit_system.DECOMP_DIR,
        "fiche_de_paie_decomposition.xml"
        )

    decomposition_json = get_decomposition_json(xml_file_path, tax_benefit_system)
    data_frame = data_frame_from_decomposition_json(
        reform_simulation,
        decomposition_json = decomposition_json,
        reference_simulation = reference_simulation,
        remove_null = True)
    return data_frame


def test_fiche_de_paie_bareme(bareme=True):
    reform_simulation, reference_simulation = create_simulation(bareme=bareme)
    xml_file_path = os.path.join(
        tax_benefit_system.DECOMP_DIR,
        "fiche_de_paie_decomposition.xml"
        )
    decomposition_json = get_decomposition_json(xml_file_path, tax_benefit_system)
    data_frame = data_frame_from_decomposition_json(
        reference_simulation,
        decomposition_json = decomposition_json,
        remove_null = True)
    return data_frame


if __name__ == '__main__':
    # test()
    # df = test_remove_null()
    df = test_fiche_de_paie_bareme()
    print df

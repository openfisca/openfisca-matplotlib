# -*- coding: utf-8 -*-


from __future__ import division


import os

from openfisca_core.decompositions import get_decomposition_json
from openfisca_france import FranceTaxBenefitSystem

from openfisca_matplotlib.tests.test_graphs import create_simulation
from openfisca_matplotlib.dataframes import data_frame_from_decomposition_json


tax_benefit_system = FranceTaxBenefitSystem()


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
        os.path.dirname(tax_benefit_system.decomposition_file_path),
        "fiche_de_paie_decomposition.xml"
        )
    decomposition_json = get_decomposition_json(tax_benefit_system, xml_file_path)
    data_frame = data_frame_from_decomposition_json(
        reform_simulation,
        decomposition_json = decomposition_json,
        reference_simulation = reference_simulation,
        remove_null = True)
    return data_frame


def test_fiche_de_paie_bareme(bareme=True):
    reform_simulation, reference_simulation = create_simulation(bareme=bareme)
    xml_file_path = os.path.join(
        os.path.dirname(tax_benefit_system.decomposition_file_path),
        "fiche_de_paie_decomposition.xml"
        )
    decomposition_json = get_decomposition_json(tax_benefit_system, xml_file_path)
    data_frame = data_frame_from_decomposition_json(
        reference_simulation,
        decomposition_json = decomposition_json,
        remove_null = True)
    return data_frame


if __name__ == '__main__':
    # test()
    # df = test_remove_null()
    df = test_fiche_de_paie_bareme()
    print(df)

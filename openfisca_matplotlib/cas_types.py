# coding: utf-8

from __future__ import division

from datetime import date
import pandas as pd
from pprint import pprint


import openfisca_france
from openfisca_core import periods
from openfisca_france.reforms.inversion_directe_salaires import TAUX_DE_PRIME

tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()


smic_horaire_by_year, smic_annuel_by_year = dict(), dict()
smic_horaire_by_year = dict([
    (
        year,
        tax_benefit_system.parameters(periods.period(year).start).cotsoc.gen.smic_h_b
        )
    for year in range(2005, 2018)
    ])

smic_annuel_by_year = dict([
    (
        year,
        value * 35 * 52,
        )
    for year, value in smic_horaire_by_year.iteritems()
    ])


def print_smcis():
    pprint(smic_horaire_by_year)
    pprint(smic_annuel_by_year)


def create_adulte(moins_de_25_ans = False, temps_partiel = False, union_legale = False, year = None, actif = False):
    assert year is not None
    parent = dict(
        date_naissance = date(year - 40, 1, 1) if not moins_de_25_ans else date(year - 23, 1, 1),
        statut_marital = "marie" if union_legale else 'celibataire',
        )

    if actif:
        activite = dict(
            activite = "actif",
            allegement_cotisation_allocations_familiales_mode_recouvrement = "fin_d_annee",
            allegement_fillon_mode_recouvrement = "fin_d_annee",
            categorie_salarie = "prive_non_cadre",
            contrat_de_travail = "temps_partiel" if temps_partiel else "temps_plein",  # CDI
            contrat_de_travail_duree = "cdi",  # CDI
            cotisation_sociale_mode_recouvrement = "mensuel_strict",
            depcom_entreprise = "75114",
            effectif_entreprise = 25,
            entreprise_assujettie_is = True,
            taux_accident_travail = .015,
            #
            aah = 0,
            caah = 0,
            rpns_individu = 0,
            rpns = 0,
            )
        return merge_dicts(parent, activite)

    else:
        return parent


def create_logement(loyer = None, loyer_fictif = None, statut_occupation_logement = None, zone_apl = None):
    if loyer or zone_apl or statut_occupation_logement:
        assert (loyer and zone_apl and statut_occupation_logement) or (loyer_fictif and statut_occupation_logement)
        menage = dict(
            loyer = loyer * 12 * 3 if loyer else None,
            loyer_fictif = loyer_fictif * 12 * 3 if loyer_fictif else None,
            statut_occupation_logement = statut_occupation_logement,
            zone_apl = zone_apl if zone_apl else None,
            )
        return menage
    else:
        return None


def create_incomplete_scenario_kwargs(biactif = False, couple = False, loyer = None, loyer_fictif = None,
        nb_enfants = 0, parent1_25ans = True, parent2_25ans = True, statut_occupation_logement = None,
        temps_partiel = False, union_legale = True, year = None, zone_apl = None):

    assert year is not None
    menage = create_logement(
        loyer = loyer,
        loyer_fictif = loyer_fictif,
        statut_occupation_logement = statut_occupation_logement,
        zone_apl = zone_apl,
        )

    return dict(
        parent1 = create_adulte(
            actif = True,
            moins_de_25_ans = not parent1_25ans,
            temps_partiel = temps_partiel,
            union_legale = union_legale & couple,
            year = year,
            ),
        parent2 = create_adulte(
            actif = biactif,
            moins_de_25_ans = not parent2_25ans,
            temps_partiel = temps_partiel,
            union_legale = union_legale,
            year = year,
            ) if couple else None,
        enfants = [dict(date_naissance = date(2014 - age, 1, 1)) for age in range(5, 15)][:nb_enfants],
        menage = menage,
        )


def create_scenario_inferieur_smic(biactif = False, couple = False, loyer = None, loyer_fictif = None, nb_enfants = 0,
        parent1_25ans = True, parent2_25ans = True, count = 10, statut_occupation_logement = None, union_legale = True,
        year = None, zone_apl = None):

    assert year is not None
    une_heure = 1 * 12
    temps_plein = 35 * 52

    scenario_kwargs = create_incomplete_scenario_kwargs(
        biactif = biactif,
        couple = couple,
        nb_enfants = nb_enfants,
        parent1_25ans = parent1_25ans,
        parent2_25ans = parent2_25ans,
        temps_partiel = True,
        union_legale = union_legale,
        year = year,
        loyer = loyer,
        loyer_fictif = loyer_fictif,
        statut_occupation_logement = statut_occupation_logement,
        zone_apl = zone_apl,
        )
    additionnal_scenario_kwargs = dict(
        axes = [[
            dict(
                count = count,
                min = une_heure,
                max = temps_plein,
                name = 'heures_remunerees_volume',
                period = year - 2,
                ),
            dict(
                count = count,
                min = une_heure,
                max = temps_plein,
                name = 'heures_remunerees_volume',
                period = year - 1,
                ),
            dict(
                count = count,
                min = une_heure,
                max = temps_plein,
                name = 'heures_remunerees_volume',
                period = year,
                ),
            dict(
                count = count,
                min = smic_horaire_by_year[year - 2] * une_heure,
                max = smic_horaire_by_year[year - 2] * temps_plein,
                name = 'salaire_de_base',
                period = year - 2,
                ),
            dict(
                count = count,
                index = 1 if biactif else None,
                min = smic_horaire_by_year[year - 2] * une_heure,
                max = smic_horaire_by_year[year - 2] * temps_plein,
                name = 'salaire_de_base',
                period = year - 2,
                ),
            dict(
                count = count,
                min = smic_horaire_by_year[year - 1] * une_heure,
                max = smic_horaire_by_year[year - 1] * temps_plein,
                name = 'salaire_de_base',
                period = year - 1,
                ),
            dict(
                count = count,
                index = 1 if biactif else None,
                min = smic_horaire_by_year[year - 1] * une_heure,
                max = smic_horaire_by_year[year - 1] * temps_plein,
                name = 'salaire_de_base',
                period = year - 1,
                ),
            dict(
                count = count,
                min = smic_horaire_by_year[year] * une_heure,
                max = smic_horaire_by_year[year] * temps_plein,
                name = 'salaire_de_base',
                period = year,
                ),
            dict(
                count = count,
                index = 1 if biactif else None,
                min = smic_horaire_by_year[year] * une_heure,
                max = smic_horaire_by_year[year] * temps_plein,
                name = 'salaire_de_base',
                period = year,
                ),
            ]],
        # period = 'year:{}:3'.format(year - 2),
        period = year,
        )

    scenario_kwargs.update(additionnal_scenario_kwargs)
    return scenario_kwargs


def create_scenario_superieur_smic(biactif = False, categorie_salarie = 'prive_non_cadre', couple = False,
        loyer = None, loyer_fictif = None, nb_enfants = 0, nb_smic_max = 2, parent1_25ans = True, parent2_25ans = True,
        count = 10, statut_occupation_logement = None, union_legale = True, year = None, zone_apl = None):

    assert year is not None

    if isinstance(categorie_salarie, str):
        categories_salarie = [
            u"prive_non_cadre",
            u"prive_cadre",
            u"public_titulaire_etat",
            u"public_titulaire_militaire",
            u"public_titulaire_territoriale",
            u"public_titulaire_hospitaliere",
            u"public_non_titulaire",
            ]
        assert categorie_salarie in categories_salarie[:3]

    name_prime = None
    if categorie_salarie in [u"prive_non_cadre", u"prive_cadre"]:
        name_salaire = 'salaire_de_base'
        # name_prime =
    else:
        name_salaire = 'traitement_indiciaire_brut'
        name_prime = 'primes_fonction_publique'

    scenario_kwargs = create_incomplete_scenario_kwargs(
        biactif = biactif, couple = couple, nb_enfants = nb_enfants,
        parent1_25ans = parent1_25ans, parent2_25ans = parent2_25ans, union_legale = union_legale, year = year,
        loyer = loyer,
        loyer_fictif = loyer_fictif,
        statut_occupation_logement = statut_occupation_logement,
        zone_apl = zone_apl,
        )

    additionnal_kwargs = dict(
        categorie_salarie = categorie_salarie,
        )
    scenario_kwargs['parent1'].update(additionnal_kwargs)
    if biactif:
        scenario_kwargs['parent2'].update(additionnal_kwargs)

    axes = list()
    for axe_year in range(year - 2, year + 1):
        axes.append(
            dict(
                count = count,
                min = smic_annuel_by_year[axe_year],
                max = smic_annuel_by_year[axe_year] * nb_smic_max,
                name = name_salaire,
                period = axe_year,
                )
            )
        if name_prime:
            axes.append(
                dict(
                    count = count,
                    min = smic_annuel_by_year[axe_year] * TAUX_DE_PRIME,
                    max = smic_annuel_by_year[axe_year] * nb_smic_max * TAUX_DE_PRIME,
                    name = name_prime,
                    period = axe_year,
                    )
                )
        if biactif:
            axes.append(
                dict(
                    count = count,
                    index = 1,
                    min = smic_annuel_by_year[axe_year],
                    max = smic_annuel_by_year[axe_year] * nb_smic_max,
                    name = name_salaire,
                    period = axe_year,
                    )
                )

    additionnal_scenario_kwargs = dict(
        axes = [axes],
        # period = 'year:{}:3'.format(year - 2),
        period = year
        )
    scenario_kwargs.update(additionnal_scenario_kwargs)

    return scenario_kwargs


def calculate(variables = None, scenarios_kwargs = None, period = None, tax_benefit_system = None, reform = None):
    assert variables is not None
    assert period is not None
    assert isinstance(scenarios_kwargs, list)
    if tax_benefit_system is None:
        tax_benefit_system = tax_benefit_system
    if reform is not None:
        tax_benefit_system = reform(tax_benefit_system)

    data_frames = list()
    for scenario_kwargs in scenarios_kwargs:
        data_frame = pd.DataFrame()
        scenario = tax_benefit_system.new_scenario().init_single_entity(**scenario_kwargs)
        simulation = scenario.new_simulation()

        for variable in variables:
            count = scenario_kwargs['axes'][0][0]['count']
            array = simulation.calculate_add(variable, period = period)
            nb_person = int(array.shape[0] / count)
            if nb_person != 1:
                data_frame[variable] = sum(
                    array[i::nb_person] for i in range(0, nb_person)
                    )
            else:
                data_frame[variable] = simulation.calculate_add(variable, period = period)

        data_frames.append(data_frame)

    return pd.concat(data_frames).reset_index(drop = True)


# helpers

def merge_dicts(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


if __name__ == '__main__':
    year = 2012
    period = year
    variables = [
        'revenu_disponible',
        'revenus_du_travail',
        'pensions',
        'revenus_du_capital',
        'aides_logement',
        'minima_sociaux',
        'salaire_net',
        'prestations_sociales',
        'ppe',
        'impots_directs',
        'loyer_fictif',
        ]
    scenario_superieur_smic = create_scenario_superieur_smic(
        year = year,
        couple = True,
        nb_enfants = 1,
        loyer_fictif = 500,
        statut_occupation_logement = 2,
        )
    scenarios_kwargs = [scenario_superieur_smic]
    df = calculate(variables, scenarios_kwargs, period)

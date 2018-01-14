# -*- coding: utf-8 -*-


import pandas as pd

from openfisca_core.parameters import Parameter, ParameterNode
from openfisca_france import FranceTaxBenefitSystem


tax_benefit_system = FranceTaxBenefitSystem()


def create_series_from_parameter(parameter):
    assert isinstance(parameter, Parameter)
    value_by_period = dict(
        (parameter_at_instant.instant_str, parameter_at_instant.value)
        for parameter_at_instant in parameter.values_list
        )
    return pd.Series(value_by_period, name = parameter.name).sort_index(ascending = False)


def create_dataframe_from_parameter_node(parameter_node):
    if isinstance(parameter_node, Parameter):
        return create_series_from_parameter(parameter_node)
    else:
        assert isinstance(parameter_node, ParameterNode)
        children_dataframes = [
            create_dataframe_from_parameter_node(parameter)
            for parameter in parameter_node.children.values()
            ]
        return (pd.concat(children_dataframes, axis = 1)
            .fillna(method = 'ffill')
            .sort_index(ascending = False)
            )


parameter_node = tax_benefit_system.parameters.prestations.aides_logement.ressources

df = create_dataframe_from_parameter_node(parameter_node)

leaf_1 = leaf = tax_benefit_system.parameters.prestations.aides_logement.ressources.dar_1
leaf_2 = leaf = tax_benefit_system.parameters.prestations.aides_logement.ressources.dar_2

series_1 = create_series_from_parameter(leaf_1)
series_2 = create_series_from_parameter(leaf_2)
series = [series_1, series_2]

print df

BOUM


leaf = tax_benefit_system.parameters.prestations.aides_logement.ressources.dar_1
node = tax_benefit_system.parameters.bourses_education.bourse_college
leaf = tax_benefit_system.parameters.bourses_education.bourse_college.montant_taux_3
print type(node)
print type(leaf)

create_series_from_parameter(node)
BIM
print leaf.__dict__.keys()
print(leaf.description.encode('utf-8'))

df = pd.DataFrame()
for name, parameter in parameter_by_name.iteritems():
    value_by_period = dict(
        (parameter_at_instant.instant_str, parameter_at_instant.value)
        for parameter_at_instant in parameter.values_list
        )

    data = pd.DataFrame.from_dict(value_by_period, orient = 'index')
    data.rename(columns = {0: name}, inplace = True)
    df = pd.concat([df, data], axis = 1)
    df.sort_index(inplace = True)

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


import pandas

from openfisca_core import decompositions
from openfisca_matplotlib.utils import OutNode


def data_frame_from_decomposition_json(simulation, decomposition_json = None, reference_simulation = None,
        remove_null = False, label = True, name = False):
    # currency = simulation.tax_benefit_system.CURRENCY # TODO : put an option to add currency, for now useless

    assert label or name, "At least label or name should be True"
    if decomposition_json is None:
        decomposition_json = decompositions.get_decomposition_json(simulation.tax_benefit_system)
    data = OutNode.init_from_decomposition_json(simulation, decomposition_json)

    index = [row.desc for row in data if row.desc not in ('root')]
    data_frame = None
    for row in data:
        if row.desc not in ('root'):
            if data_frame is None:
                value_columns = ['value_' + str(i) for i in range(len(row.vals))] if len(row.vals) > 1 else ['value']
                data_frame = pandas.DataFrame(index = index, columns = ['name'] + value_columns)

            data_frame['name'][row.desc] = row.code
            data_frame.loc[row.desc, value_columns] = row.vals

    data_frame.index.name = "label"
    if remove_null:
        variables_to_remove = []
        for variable in data_frame.index:
            if (data_frame.loc[variable, value_columns] == 0).all():
                variables_to_remove.append(variable)
        data_frame.drop(variables_to_remove, inplace = True)

    data_frame.reset_index(inplace = True)

    return data_frame

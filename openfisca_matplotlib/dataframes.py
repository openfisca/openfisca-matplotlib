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


import pandas as pd

from openfisca_matplotlib.utils import OutNode


def data_frame_from_decomposition_json(simulation, decomposition_json = None, reference_simulation = None,
                                       remove_null = False):
    currency = simulation.tax_benefit_system.CURRENCY # TODO : put an option to add currency, for now useless
    data = OutNode.init_from_decomposition_json(
        simulation = simulation,
        decomposiiton_json = decomposition_json,
    )
    data_dict = dict()
    index = []
    for row in data:
        if not row.desc in ('root'):
            index.append(row.desc)
            data_dict[row.desc] = row.vals

    data_frame = pd.DataFrame(data_dict).T
    data_frame = data_frame.reindex(index)
    data_frame.index.name = "variable"
    if len(data_frame.columns) == 1:
        data_frame.columns = ["valeur"]
    if remove_null:
        variables_to_remove = []
        for variable in data_frame.index:
            if (data_frame.loc[variable] == 0).all():
                print variable
                variables_to_remove.append(variable)

        data_frame.drop(variables_to_remove, inplace = True)

    return data_frame

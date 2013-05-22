# -*- coding:utf-8 -*-
# Created on 22 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from src.countries.france.data.erf.datatable import ErfsDataTable
year = 2009
erf = ErfsDataTable(year=year)
erf.set_config()
vars = [ "zrstm", "zchom", "pfamm", "wprm"]
df = erf.get_values(variables=vars, table="erf_menage" ) 

print df.describe()

#
#af bmaf
#rsti ipc
#santé ipc IJ
#choi smbo
#
#seuil 

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
#erf.set_config()
vars = [ "zrstm", "zchom", "pfamm", "wprm", "pauvre50m", "pauvre60m"]
df = erf.get_values(variables=vars, table="erf_menage" ) 



from pandas import DataFrame
indexes = { "zrstm" : .01, "zchom": .01, "pfamm" : .01}
results = DataFrame(index =indexes.keys(), columns = ["total", "pauvre50", "pauvre60"])


for var, index in indexes.iteritems():
    total = df[var]*index*df["wprm"]
    pauvre50 = df[var]*index*df["wprm"]*(df["pauvre50m"]<=0)
    pauvre60 = df[var]*index*df["wprm"]*(df["pauvre60m"]<=0) 
    results.set_value(var, "total", total.sum()/1e6)
    results.set_value(var, "pauvre50", pauvre50.sum()/1e6)
    results.set_value(var, "pauvre60", pauvre60.sum()/1e6)

print results
    
print df.describe()

#
#af bmaf
#rsti ipc
#santé ipc IJ
#choi smbo
#
#seuil 

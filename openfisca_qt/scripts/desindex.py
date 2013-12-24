# -*- coding:utf-8 -*-
# Created on 22 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from pandas import DataFrame, ExcelWriter
from numpy import arange
from src.lib.utils import mark_weighted_percentiles
from src.countries.france.data.erf.datatable import ErfsDataTable
from src.countries.france.data.sources.config import destination_dir

year = 2009
erf = ErfsDataTable(year=year)
#erf.set_config()
vars = [ "zrstm", "zchom", "pfamm", "wprm", "pauvre50m", "pauvre60m", "nivviem", "champm"]
df = erf.get_values(variables=vars, table="erf_menage" ) 


labels = arange(1,11)
method = 2

nivvie = df["nivviem"].astype("float64").values

wprm = df["wprm"].astype("float64").values
decil, values = mark_weighted_percentiles(nivvie, labels, wprm, method, return_quantiles = True)


df2 = DataFrame({"decile" : decil})
df["decile"] = df2["decile"]



indexes = { "zrstm" : .01, "zchom": .01, "pfamm" : .01} # TODO change 1%
results = DataFrame(index =indexes.keys(), columns = ["total", "pauvre50", "pauvre60"] + ["decile>"+str(decile) for decile in range(0,10)] )

for var, index in indexes.iteritems():
    total = df[var]*index*df["wprm"]*df["champm"]
    pauvre50 = df[var]*index*df["wprm"]*(df["pauvre50m"]<=0)*df["champm"]
    pauvre60 = df[var]*index*df["wprm"]*(df["pauvre60m"]<=0)*df["champm"] 
    results.set_value(var, "total", total.sum()/1e6)
    results.set_value(var, "pauvre50", pauvre50.sum()/1e6)
    results.set_value(var, "pauvre60", pauvre60.sum()/1e6)
    for decile in range(0,10):
        temp = df[var]*index*df["wprm"]*(df["decile"]>decile)*df["champm"]
        results.set_value(var, "decile>"+str(decile), temp.sum()/1e6)
        del temp

print results
import os
filename = os.path.join(destination_dir,"desindexation.xls")
print filename
writer = ExcelWriter(str(filename))
results.to_excel(writer)
writer.save()


#
#af bmaf
#rsti ipc
#santé ipc IJ
#choi smbo
#
#seuil 

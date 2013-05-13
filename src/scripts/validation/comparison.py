# -*- coding:utf-8 -*-
# Created on 17 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from __future__ import division
from src.lib.simulation import SurveySimulation 
from src.countries.france.data.erf.datatable import ErfsDataTable




    #def test_demography():
    #    #  Demographic characteristics
    #    #    number of households/foyers compared to erf (and other sources recensement ? careful with champm variable)
    #    
    #    merged_df["diff"] = merged_df["af"] - merged_df["m_afm"]
    #    print merged_df["diff"].describe()
    #    print "non nul :", (merged_df["diff"] != 0).sum()
    #    print " < -400 :", (merged_df["diff"] <= -400).sum()
    #    diff = merged_df.loc[merged_df["diff"] != 0, ["diff","wprm"]]
    #    print diff.describe(percentile_width=80)
    #    return
    #
    #
    #    wprm_of_men = wprm.sum()
    #    wprm_erf_men = df.wprm.sum()
    #    print wprm_erf_men, wprm_of_men
    #    
    #    wprm_champm_of_men = (wprm*champm).sum()
    #    wprm_champm_erf_men = (df.wprm*df.champm).sum()
    #    print wprm_champm_erf_men, wprm_champm_of_men
    #
    #    af_of_men = (af.af).sum()
    #    af_erf_men = (df["m_afm"]).sum()
    #    print af_erf_men/1e9, af_of_men/1e9
    #    
    #
    #    df = df.astype('float64')
    #
    #    af_of_men = (af.af*wprm).sum()
    #    af_erf_men = (df["m_afm"]*df.wprm*df.champm).sum()
    #    print af_erf_men/1e9, af_of_men/1e9
    #    
    #    
    #    #    types of household compared to erf
    #    #    age structure of population  scripts.sandbox.age_structure.py
    #
    #    
    #
    #    
    #    # Post-computation validation
    #    #
    #    #  Check for every prestation the equivalence/differneces of concept definition
    #    #  Decompose cotsoc (in the code TODO: MBJ LB ?)
    #    #  Decompose impot sur le revenu to check intermediate aggregates vs fiscal data and erf
    #    #  Check downward prestation one by one

def compare_of_erf(variables, year = 2006):
    """
    Compare variables in erf an openfisca
    """
    country = "france"
    simulation = SurveySimulation()
    simulation.set_config(year = year, country = country)
    simulation.set_param()
    simulation.set_survey()
    simulation.compute()
    
    erf = ErfsDataTable()
    erf.set_config(year=year)
    if "ident" not in variables:
        erf_variables = variables + ["ident"]
    else:
        erf_variables = variables
        
    if "wprm" not in erf_variables:
        erf_variables = erf_variables + ["wprm"]
    else:
        erf_variables = erf_variables    
    
    erf_dataframe = erf.get_values(erf_variables, table="menage")
    erf_dataframe.rename(columns={'ident': 'idmen'}, inplace=True)
    for col in erf_dataframe.columns:
        if col is not "idmen":
            erf_dataframe.rename(columns={col: col + "_erf"}, inplace=True)
    
    of_dataframe, of_dataframe_default = simulation.aggregated_by_entity("men", variables, all_output_vars=False, force_sum=True)
    del of_dataframe_default

    merged_df = of_dataframe.merge(erf_dataframe, on="idmen" )
    print merged_df 
    

if __name__ == '__main__':

#    test_demography()
    variables = [ "nbinde", "typmen15"]
    compare_of_erf(variables)
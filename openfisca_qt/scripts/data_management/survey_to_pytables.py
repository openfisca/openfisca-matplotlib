'''
Export survey<hh in a Pytables format from which ViTables can be used to visualise initial data.

@author: Alexis Eidelman
'''


from openfisca_france.data.sources.config import destination_dir
import tables
import pdb
import os
from pandas import HDFStore

from openfisca_core import model
from openfisca_core.simulations import SurveySimulation


filename = os.path.join(model.DATA_DIR, 'survey3.h5')

num_table = 3


input = HDFStore(filename)
survey = tables.openFile(destination_dir+"survey3.h5", mode = "w")

years = ['2006']

for yr in years:
    simu = SurveySimulation()
    simu.set_config(year = yr)
    simu.set_param()
    simu.set_survey(num_table=num_table)
    survey_year = survey.createGroup("/", "survey_"+yr,"year")
    if num_table == 3:
        for ent in ['ind','men','foy','fam']:
            tab = simu.survey.table3[ent]
            tab_type = tab.to_records(index=False).dtype
            survey_table = survey.createTable('/survey_'+yr,ent,tab_type)
            survey_table.append(tab.to_records(index=False))
            survey_table.flush()
    if num_table == 1:
        tab = simu.survey.table
        tab_type = tab.to_records(index=False).dtype
        to_remote = ['opt_colca','quelfic']
        for x in tab_type.descr:
            if x[1] == '|b1' :
                to_remote = to_remote + [x[0]]
        tab.drop(to_remote, axis=1, inplace=True)
        tab_type = tab.to_records(index=False).dtype
        survey_table = survey.createTable('/survey_'+yr,'table',tab_type)
        survey_table.append(tab.to_records(index=False))
        survey_table.flush()



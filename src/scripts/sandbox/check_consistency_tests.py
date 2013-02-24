# -*- coding:utf-8 -*-
# Created on 17 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from src.lib.simulation import SurveySimulation 

def test():
    
    from numpy import unique, sum
        
    for yr in range(2008,2009):
        country = 'france'
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()
        simu.set_survey()
        
        survey = simu.survey
        # Numbers of menages
        ENTITIES_INDEX = ['men', 'fam', 'foy']
        print yr
        print len(survey.get_value('noi'))
#        print unique(survey.get_value('noi'))
#        print len(unique(survey.get_value('noi')))
        for entity in ENTITIES_INDEX:        
            id = survey.get_value('id' + entity)
            print id.dtype
            head = survey.get_value('qui' + entity)
            print head.dtype
            n_id = len(unique(id))
            n_head = sum(head == 0)
             
            if n_id != n_head:
                print 'incoherence for ' + entity + ' : id =' + str(n_id) +' and heads=' + str(n_head)
        
        
        
        # Problemes
        # enfants de plus de 21 ans et parents à charge dans les fmailles avec quifam=0
if __name__ == '__main__':

    test()

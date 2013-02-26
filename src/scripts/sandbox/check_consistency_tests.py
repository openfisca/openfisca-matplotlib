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
        
    for yr in range(2006,2007):
        country = 'france'
        simulation = SurveySimulation()
        simulation.set_config(year = yr, country = country)
        simulation.set_param()
        simulation.set_survey()
        
        survey = simulation.survey
        
        ENTITIES_INDEX = ['men', 'fam', 'foy']
        print 'Year of the data: ' +  str(yr)
        # print len(survey.get_value('noi'))
        for entity in ENTITIES_INDEX:        
            id = survey.get_value('id' + entity)
            head = survey.get_value('qui' + entity)
            n_id = len(unique(id))
            n_head = sum(head == 0)
            if n_id != n_head:
                print 'incoherence for ' + entity + ' : id =' + str(n_id) +' and heads=' + str(n_head)
        

        # verifying the age of childrens
        quifam = survey.get_value('quifam')
        age = survey.get_value('age')
        if sum((quifam >= 2) & (age >= 21)) != 0:
            print "they are kids that are of age >= 21"

        from src.lib.utils import of_import
        WEIGHT = of_import("","WEIGHT", simulation.country)
        weight = survey.get_value(WEIGHT)
        if sum(weight<=0) != 0:
            print "some weights are zero"
        # Problemes
        # enfants de plus de 21 ans et parents à charge dans les fmailles avec quifam=0

        idmen = survey.get_value('idmen')
        from numpy import max as max_
        print max_(idmen)

if __name__ == '__main__':

    test()

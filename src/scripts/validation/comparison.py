# -*- coding:utf-8 -*-
# Created on 17 févr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from src.lib.simulation import SurveySimulation 
from src.lib.utils import of_import
from pandas import concat


if __name__ == '__main__':
    year = 2006
    country = "france"
    simulation = SurveySimulation()
    simulation.set_config(year = year, country = country)
    simulation.set_param()
    simulation.set_survey()
    
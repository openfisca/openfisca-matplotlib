# -*- coding:utf-8 -*-
"""
Created on Nov 30, 2012
@author: Mahd Ben Jelloul

openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

# imports from openfisca
from core.datatable import DataTable, SystemSf

from parametres.paramData import XmlReader, Tree2Object
from Config import CONF
from france.utils import Scenario
from france.model.data import InputTable
from france.model.model import ModelSF
from core.utils import gen_output_data, gen_aggregate_output, of_import



import gc

class Simulation(object):
    """
    A simulation objects should contains all attributes to compute a simulation from a scenario or a survey
    It should also provide results that can be used by other functions
    """
    
    def __init__(self):
        super(Simulation, self).__init__()


        self.scenario = None
        self.survey = None

        self.datesim = None
        self.nmen = None

        self.country = None
        self.P = None
        self.P_default = None
        self.totaux_fnane = None
        self.param_file = None
    
    def set_config(self, **kwargs):
        '''
        Sets the directory where to find the openfisca source and adjust some directories
        '''
#        if directory is None:
#            cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
#            predirectory = os.path.dirname(cmd_folder)
#            directory = os.path.join(predirectory,'../../srcopen')
#        
#        
#        CONF.set('paths', 'data_dir', os.path.join(directory,'data'))

        if nmen is None:
            nmen = 1
        
        CONF.set('simulation', 'nmen', nmen)

        self.set_date(date)



#        self.set_config(directory = root_dir)        
        self.set_survey( year = year)

        
    def build(self):
        self.set_date()
        msg = self.scenario.check_consistency()
        if msg:
            print 'inconsistent scenario'
        self.set_param()
        self.compute()
                
         
    def set_scenario(self, scenario=None):
        if scenario is None:
            self.scenario = Scenario()
        else:
            self.scenario = scenario  
        
    def set_survey(self, year = None, filename = None):
        NotImplementedError
        
    def set_date(self, date = None):
        if date == None:
            self._date = CONF.get('simulation', 'datesim')
        else:
            self._date = date
            CONF.set('simulation', 'datesim', str(self._date))
        print self._date
        
    def set_param(self):
        '''
        Sets the parameters of the simulation
        '''
        reader = XmlReader(self.param_file, self._date)
        rootNode = reader.tree
        
        self.P_default = Tree2Object(rootNode, defaut = True)
        self.P_default.datesim = self._date

        self.P = Tree2Object(rootNode, defaut = False)
        self.P.datesim = self._date
              
  
    def compute(self):
        '''
        Computes the aggregates  
        '''
        if (self.scenario is not None) and (self.survey is not None):
            print 'error scenario and survey are both not None'
            return False
        
        if self.scenario is not None:
            return self.compute_from_scenario()
        elif self.survey is not None:
            return self.compute_from_survey()
        else:
            return False
            print 'Both survey and scenario are None'



    def compute_from_scenario(self):
        """
        Computes output_data from scenario
        """
        input_table = DataTable(InputTable, scenario = self.scenario)
        population_courant = SystemSf(ModelSF, self.P, self.P_default)
        population_courant.set_inputs(input_table)
        return gen_output_data(population_courant, self.totaux_fname)
        
    def compute_from_survey(self):
        """
        Computes output_data from scenario
        """
        
        # Clear outputs
        self.survey_outputs = None
        self.survey_outputs_default = None
        gc.collect()

        self.survey_outputs, self.survey_outputs_default = self.calculate_all()
        
        # Compute aggregates
        data = gen_aggregate_output(self.survey_outputs)
        descr = [self.survey.description, self.survey_outputs.description]
        data_default = None
        if self.reforme:
            data_default = gen_aggregate_output(self.survey_outputs_default)

        return data, data_default

    def preproc(self, input_table):
        '''
        Prepare the output values according to the ModelSF definitions/Reform status/input_table
        '''
        P_default = self.P_default # _parametres.getParam(defaut = True)    
        P         = self.P         # _parametres.getParam(defaut = False)
        
        output = SystemSf(self.ModelSF, P, P_default)
        output.set_inputs(input_table)
                
        if self.reforme:
            output_default = SystemSf(self.ModelSF, P_default, P_default)
            output_default.set_inputs(input_table)
        else:
            output_default = output
    
        return output, output_default

            

    def calculate_all(self):
        '''
        Computes all prestations
        '''
        input_table = self.survey
        output, output_default = self.preproc(input_table)
        
        output.calculate()
        if self.reforme:
            output_default.reset()
            output_default.calculate()
        else:
            output_default = output
    
        return output, output_default




if __name__ == '__main__':


    
    
    
    years = ['2006', '2007', '2008', '2009']
    for yr in years:
        
    pass
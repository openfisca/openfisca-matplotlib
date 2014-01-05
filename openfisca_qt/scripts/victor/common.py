# -*- coding:utf-8 -*-


import os
import pickle

from openfisca_core import model
from pandas import HDFStore


def load_content(name, filename):
    """
    Loads dataframes from an HDF store
    and simulation attributes from a pk file.
    See save_content function.

    WARNING : Be careful when committing, you may have created a .pk data file.

    Parameters
    ----------
    name : the base name of the content inside the store.
    We load an output_table, an input_table, and the default output_table.
    filename : the name of the .h5 file where the table is stored. Created if not existant.
    """

    print 'Loading content for simulation from file %s' %filename
    with open(filename + '.pk', 'rb') as input:
        simu = pickle.load(input)

    ERF_HDF5_DATA_DIR = os.path.join(model.DATA_DIR, 'erf')
    store = HDFStore(os.path.join(os.path.dirname(ERF_HDF5_DATA_DIR),filename+'.h5'))
    simu.output_table.table = store[name + '_output_table']
    simu.input_table.table = store[name + '_input_table']
    simu.output_table_default.table = store[name + '_output_table_default']
    return simu

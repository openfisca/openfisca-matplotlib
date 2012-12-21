# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
µSim, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul


This file is part of µSim.

    µSim is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    µSim is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with µSim.  If not, see <http://www.gnu.org/licenses/>.
"""

from distutils.core import setup
from Config import VERSION
import py2exe
import matplotlib
import os
import glob


def find_data_files(source,target,patterns):
    """
    Locates the specified data-files and returns the matches
         in a data_files compatible format.
 
     source is the root of the source data tree.
        Use '' or '.' for current directory.
     target is the root of the target data tree.
        Use '' or '.' for the distribution directory.
     patterns is a sequence of glob-patterns for the
     files you want to copy.
    """
    if glob.has_magic(source) or glob.has_magic(target):
        raise ValueError("Magic not allowed in src, target")
    ret = {}
    for pattern in patterns:
        pattern = os.path.join(source,pattern)
        for filename in glob.glob(pattern):
            if os.path.isfile(filename):
                targetpath = os.path.join(target,os.path.relpath(filename,source))
                path = os.path.dirname(targetpath)
                ret.setdefault(path,[]).append(filename)
    return sorted(ret.items())

# Example:
#setup(
#    name="Sample",
#    version="1.0",
#    description="A sample app",
#    author="MizardX",
#    console=['samplescript.py'],
#    data_files=find_data_files('data','',[
#        'README',
#        'images/*',
#    ]),
#)

# Will copy data/README to dist/README, and all files in data/images/ to dist/images/
# (not checking any subdirectories of data/images/)


dist_dir = "c:/users/utilisateur/documents/OpenFisca-%s-x64" % VERSION
data_files = matplotlib.get_py2exe_datafiles()

countries = ['france'] # countries = ['france', 'tunisia'] 

tuples_list = []

for country in countries:
    
    model = find_data_files('./%s/model/' %country,
                               '%s/model/' %country,
                               ['*.py'])
    tuples_list.append(model[0])
    
    castypes = find_data_files('./%s/castypes/' %country,
                                '%s/castypes/' %country,
                                ['*.ofct'])
    tuples_list.append(castypes[0])
    
    param = find_data_files('./%s/param/' %country,
                                '%s/param/' %country,
                                ['param.xml'])
    tuples_list.append(param[0])

    reformes = find_data_files('./%s/reformes/' %country,
                                '%s/reformes/' %country,
                                ['*.ofp'])
    tuples_list.append(reformes[0])
    totaux = find_data_files('./%s/' %country,
                                '%s/' %country,
                                ['totaux.xml'])
    tuples_list.append(totaux[0])

    if country == 'france':
        calibrations = find_data_files('./france/calibrations/',
                                       './france/calibrations/',
                                       ['*.csv'])
        tuples_list.append(calibrations[0])
        data = find_data_files('./france/data/',
                               './france/data/',
                               ['*.csv', 'amounts.h5', 'actualisation_groups.h5'])
        tuples_list.append(data[0])
        data_sources = find_data_files('./france/data/sources/',
                                       './france/data/sources/',
                                       ['*.xls'])
        tuples_list.append(data_sources[0])
        
for tupl in tuples_list:
    data_files.append(tupl)


print dist_dir
setup(windows=[{
                "script" : "openFisca.pyw"
                }], 
      options={"py2exe" : {"includes" : ["sip", "encodings.*", "numpy.*"],
                           "dist_dir": dist_dir,
                           "packages": ["france","tunisia"],
                           "bundle_files":3,
                           "dll_excludes": ["MSVCP90.dll"]
                           }}, 
      data_files=data_files)

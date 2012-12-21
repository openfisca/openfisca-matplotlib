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

myDataFiles = matplotlib.get_py2exe_datafiles()
myDataFiles.append(("data",["data/param.xml",  "data/code_apl", "data/totaux.xml", "data/calage_men.csv", "data/calage_pfam.csv"]))
for f in os.listdir('castypes'):
    myDataFiles.append(('castypes', ['castypes/' + f]))
for f in os.listdir('reformes'):
    myDataFiles.append(('reformes', ['reformes/' + f]))
for f in os.listdir('calibrations'):
    myDataFiles.append(('calibrations', ['calibrations/' + f]))
setup(windows=[{
                "script" : "openFisca.pyw"
                }], 
      options={"py2exe" : {"includes" : ["sip", "encodings.*", "numpy.*"],
                           "dist_dir": "C:/users/utilisateur/documents/OpenFisca-%s-win32" % VERSION,
                           "bundle_files":1}}, 
      data_files=myDataFiles)

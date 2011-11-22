# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
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
from Config import VERSION
from distutils.core import setup
import py2exe
import matplotlib
import os

myDataFiles = matplotlib.get_py2exe_datafiles()
myDataFiles.append(("data",["data/param.xml", "data/code_apl", "data/totaux.xml"]))
for f in os.listdir('castypes'):
    myDataFiles.append(('castypes', ['castypes/' + f]))
for f in os.listdir('reformes'):
    myDataFiles.append(('reformes', ['reformes/' + f]))
setup(windows=[{
                "script" : "openFisca.pyw"
                }], 
      options={"py2exe" : {"includes" : ["sip", "encodings.*", "tables.*", "numpy.*"],
                           "dist_dir": "C:/users/utilisateur/dist/openFisca-%s" % VERSION,
                           "bundle_files":1}}, 
      data_files=myDataFiles)

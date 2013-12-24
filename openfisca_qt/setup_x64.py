# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
OpenFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul


This file is part of OpenFisca.

    OpenFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    µSim is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

from distutils.core import setup
from src import __version__ as VERSION

from src.setup import build_datafiles



dist_dir = "c:/users/utilisateur/documents/OpenFisca-%s-x64" % VERSION
countries = ['france'] # countries = ['france', 'tunisia'] 
data_files = build_datafiles(countries)


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

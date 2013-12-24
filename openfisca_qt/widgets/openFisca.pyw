# /usr/bin/env python
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

from PyQt4.QtGui import QApplication
from src.widgets.MainWindow import MainWindow

def main():
    import sys
    app = QApplication(sys.argv)
    app.setOrganizationDomain("www.openfisca.fr")
    app.setApplicationName("OpenFisca")
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()

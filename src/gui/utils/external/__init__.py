# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
sr.gui.utils.external
========================

External libraries needed for Spyder to work.
Put here only untouched libraries, else put them in utils.
"""

import sys
from src.gui.baseconfig import get_module_source_path
sys.path.insert(0, get_module_source_path(__name__))
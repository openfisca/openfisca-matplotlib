# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

# Generates the pot files in the src.locale directory
# Translation are to be in the languages directories by updating the .po files

try:
    from guidata.gettext_helpers import do_rescan, do_rescan_files
except ImportError:
    raise ImportError, "This script requires guidata >= v1.3.0."


if __name__ == "__main__":    
    do_rescan("src")
#    do_rescan_files(["spyderplugins/p_pylint.py",
#                     "spyderplugins/widgets/pylintgui.py"],
#                     "p_pylint", "spyderplugins")
#    do_rescan_files(["spyderplugins/p_profiler.py",
#                     "spyderplugins/widgets/profilergui.py"],
#                     "p_profiler", "spyderplugins")

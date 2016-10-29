"""Sets up the Hiero environment for CBSD and imports common modules.

@details Excluding other non-alphanumeric characters, the name "0.py" ensures
         that this module will be loaded first.  For each path in the
         environment variable HIERO_PLUGIN_PATH, Hiero 1.8 loads plugin scripts
         in the Python/Startup folder followed by the Python/StartupUI folder
         into hiero.plugins.  The script loading priority is given to filenames
         beginning with numbers, capital letters, underscores, and finally
         lower case letters.
         
@author Brendan Holt
@date December 2013

@see <a href="http://docs.thefoundry.co.uk/products/hiero/developers/1.8/hieropythondevguide/" target=_"blank">
     Hiero Python Developers Guide</a>

"""
import os
import sys

from hiero.core.find_plugins import loadPluginsFromFolder


## The absolute path to Hiero's plugin startup folder.
STARTUP_PATH = ''  # force Doxygen to use type "string" instead of "tuple"
STARTUP_PATH = os.path.dirname(__file__)

## Relative paths to external Python modules/packages.
#
#  @details Some of these paths provide supporting functionality for Hiero
#           Python plugins.
EXTERNAL_PATHS = [
    '../Wiretap',
]

# Add the locations of studio Python modules to the path
for p in EXTERNAL_PATHS:
    p = os.path.normpath(os.path.join(STARTUP_PATH, p))
    if os.path.isdir(p):
        if p not in sys.path:
            sys.path.append(p)
    else:
        raise OSError("Since the following directory does not exist, it was "
                      "not added to the Python path: " + p)

## Relative paths to Hiero plugin folders located outside of Python/Startup and
#  Python/StartupUI.
#
#  @details These allow the developer to use custom folder structures rather
#           than the specific set of nested directories required by
#           HIERO_PLUGIN_PATH.  Only those modules which register new tasks,
#           presets, menus, etc. should be loaded as plugins.  Modules which
#           provide supporting functionality (including Qt Designer forms
#           compiled with pyside-uic) should be added to the Python path
#           instead.
EXTERNAL_PLUGINS = [
    '../Wiretap/plugins',
]

# Load the external plugins.
for p in EXTERNAL_PLUGINS:
    p = os.path.normpath(os.path.join(STARTUP_PATH, p))
    loadPluginsFromFolder(p)

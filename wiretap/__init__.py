"""Loads the platform-appropriate Wiretap Python bindings.

@details The Wiretap Python extension requires the Boost.Python and dynamic
         Wiretap libraries that were both compiled for the current platform and
         Python version.

@note Autodesk refers to "Wiretap" in their SDK Documentation and product
      materials, while using the convention "WireTap" in their API.

@note For autocompletion in Eclipse, add the folder containing the proper
      version of libwiretapPythonClientAPI that was compiled for the currently
      selected interpreter to the PYTHONPATH - External Libraries list. 

"""
import os.path
import platform
import sys


LIBNAME = 'Wiretap'


def GetLibraryDirPath():
    osAbbrev = {
        'Windows': 'win',
        'Microsoft': 'win',
        'Darwin': 'osx',
        'Linux': 'linux'
    }
    
    systemOS = platform.system()
    if sys.maxsize <= 2**32:
        arch = 32
    else:
        arch = 64
    
    # Check whether the OS is in the abbreviation table
    try:
        platformFolder = osAbbrev[systemOS] + str(arch)
    except KeyError:
        msg = ("The {0} Python bindings are not available on the {1} "
               "operating system.").format(LIBNAME, systemOS)
        return '', msg
    
    # Check whether there is a folder for the platform
    pkgPath = os.path.dirname(__file__)
    curPath = os.path.join(pkgPath, platformFolder)
    if not os.path.isdir(curPath):
        msg = (
            "The {0} Python bindings have not yet been compiled for {1} "
            "{2}-bit."
        ).format(LIBNAME, systemOS, arch)
        return '', msg
    
    # Check whether there is a folder for the current Python version
    pythonFolder = 'py{0}{1}'.format(*sys.version_info[0:2])
    pythonVersion = '{0}.{1}'.format(*sys.version_info[0:2])
    curPath = os.path.join(curPath, pythonFolder)
    if not os.path.isdir(curPath):
        msg = (
            "The {0} Python bindings have not yet been compiled for "
            "Python {1} on {2} {3}-bit."
        ).format(LIBNAME, pythonVersion, systemOS, arch)
        return '', msg

    return curPath, ''

# TO DO: handle unsupported platform
__libDirPath, __errors = GetLibraryDirPath()

if __libDirPath:
    if __libDirPath not in sys.path:
        sys.path.append(__libDirPath)
else:
    raise ImportError(__errors)

from libwiretapPythonClientAPI import *


class WireTapException(Exception):
    pass


# Define here other classes/functions that are dependent on Wiretap Python API

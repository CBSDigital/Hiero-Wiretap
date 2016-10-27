"""This dummy module is imported by a command-line script in the same folder in
order to unambiguously determine the script path.

@details In Python, it is difficult for scripts running as "main" to determine
         their current path.  However, another module in a known directory can
         find the location using its \c{__file__} attribute.

@author Brendan Holt
@date June 2014
@defgroup modLocator Locator
@{

"""
import os.path

## The absolute path to the current scripts folder.
SCRIPT_PATH = ''  # force Doxygen to use type "string" instead of "tuple"
SCRIPT_PATH = os.path.dirname(__file__)


## @}

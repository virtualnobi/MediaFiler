#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2017-
"""


# Imports
## Standard
from __future__ import print_function
import logging
import gettext
import os.path
## Contributed
## nobi
## Project
import UI  # to access UI.PackagePath



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message




class ClassName(object): 
    """
    """
    

# Constants
    Logger = logging.getLogger(__name__)


# Class Variables



# Class Methods
    @classmethod
    def classMethod(clas):
        """
        """
        pass



# Lifecycle
    def __init__(self):
        """
        """
        # inheritance
        super(ClassName, self).__init__()
        # internal state



# Setters
    def setAttribute(self, value):
        """
        """
        pass
    
    

# Getters
    def getAttribute(self):  # inherited from SuperClass
        """
        """
        pass
    
    

# Event Handlers
    def updateAspect(self, observable, aspect):
        """
        """
        pass



# Inheritance - Superclass



# Other API Functions



# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



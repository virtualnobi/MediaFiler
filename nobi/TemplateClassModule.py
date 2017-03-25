#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import gettext
import os.path
## Contributed
## nobi
## Project
import UI  # to access UI.PackagePath



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
    print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message




class ClassName(object): 
    """
    """
    

# Constants
    ConstantName = 'value'


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
        return(None)



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
    def handleObservableChanged(self, observable):
        """
        """
        pass


    def handleObservableChangedAspect(self, observable, aspect):
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



#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
from __future__ import print_function
import sys
import logging
import gettext
import os.path
## Contributed
# from wx import Validator
import wx
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
    _ = Translation.gettext
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class TextCtrlIsIntValidator(wx.PyValidator): 
    """Verify that the associated TextCtrl contains an integer. 
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
#     def __init__(self, title=_('Validation Error'), label=_('Value'), minimum=(-sys.maxint-1), maximum=sys.maxint, emptyAllowed=False):
    def __init__(self, title=_('Validation Error'), label=_('Value'), minimum=(-sys.maxsize-1), maximum=sys.maxsize, emptyAllowed=False):
        """
        String title is the title of the Dialog indicating a validation error.
        String label is the text shown to indicating the erroneous field.
        Number minimum is the minimum allowed number
        Number maximum is the maximum allowed number
        Boolean emptyAllowed indicates whether the TextCtrl may be left empty
        """
        # inheritance
#        super(TextCtrlIsIntValidator, self).__init__()
        wx.PyValidator.__init__(self)
        # internal state
        self.integerValue = None
        self.validationErrorTitle = title
        self.fieldLabel = label
        self.minimumValue = minimum
        self.maximumValue = maximum
        self.emptyAllowed = emptyAllowed


    def Clone(self):
        """Overrides
        """
        return(TextCtrlIsIntValidator(title=self.validationErrorTitle, 
                                      label=self.fieldLabel, 
                                      minimum=self.minimumValue, 
                                      maximum=self.maximumValue,
                                      emptyAllowed=self.emptyAllowed))


# Setters
    def setIntegerValue(self, integer):
        self.integerValue = integer



# Getters
    def GetIntegerValue(self):
        return(self.IntegerValue)


    def Validate(self):  # inherited from SuperClass
        """Override
        """
        if (self.GetWindow().IsEnabled()):  # can trigger validation error only if enabled for input
            message = None
            self.TransferFromWindow()
            if (self.integerValue == None):
                if (not self.emptyAllowed):
                    message = _('%s requires an integer value' % self.fieldLabel)
            elif (self.integerValue < self.minimumValue): 
                message = _('%s must be an integer larger or equal to %s' % (self.fieldLabel, self.minimumValue))
            elif (self.maximumValue < self.integerValue):
                message = _('%s must be an integer smaller or equal to %s' % (self.fieldLabel, self.maximumValue))
            if (message):
                dlg = wx.MessageDialog(self.GetWindow(), message, self.validationErrorTitle, (wx.OK))
                dlg.ShowModal()
                dlg.Destroy()
                return(False)
        return(True)
    
    

# Other API Functions
    def TransferToWindow(self):
        """Override
        """
        self.GetWindow().SetValue('%s' % self.integerValue)
        return(True)

    
    def TransferFromWindow(self):
        """Overrride
        """
        try:
            self.integerValue = int(self.GetWindow().GetValue())
        except:
            self.integerValue = None
        return(True)



# Event Handlers
# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



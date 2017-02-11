# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import math
## Contributed
import wx
## nobi
## Project



class CheckBoxGroup(wx.Control): 
    """A wx.GridBagSizer containing wx.CheckBoxes.
    
    In contrast to wx.CheckListBox, it has a title and allows a grid layout, like a wx.RadioBox, but it does not have a frame. 
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
    def __init__(self, parent, ident=wx.ID_ANY, #pos=(0, 0), size=(0, 0), validator=, name='',
                 label='', choices=[], majordimension=0, style=0, 
                 vgap=0, hgap=5):
        """
        
        GridBagSizer: self, vgap, hgap
        RadioBox: self, parent, id=-1, label=EmptyString, pos=DefaultPosition, size=DefaultSize, choices=wxPyEmptyStringArray, majorDimension=0, style=RA_HORIZONTAL, validator=DefaultValidator, name=RadioBoxNameStr
        """
        # inheritance
        print parent
        super(CheckBoxGroup, self).__init__(self, parent, ident) #, pos, size, style, validator, name)
        # internal state
        checkBoxes = []
        # sizing of the grid
        if ((0 < majordimension)
            and (style & wx.RA_SPECIFY_COLS)):
            maxColumns = majordimension
            maxRows = math.floor(len(choices) / maxColumns)
        elif ((0 < majordimension) 
              and (style & wx.RA_SPECIFY_ROWS)):
            maxRows = majordimension
            maxColumns = math.floor(len(choices) / maxRows)
        else: 
            maxRows = math.ceil(math.sqrt(len(choices)))
            maxColumns = math.floor(len(choices) / maxRows)
        #
        self.SetSizer(wx.GridBagSizer(vgap=vgap, hgap=hgap))
        self.GetSizer().Add(item=wx.StaticText(self, -1, label), pos=(0,0), span=(1, maxColumns))
        row = 1
        col = 0
        for choice in choices:
            checkBox = wx.CheckBox(self, label=choice)
            checkBoxes.append(checkBox)
            self.Bind(wx.EVT_CHECKBOX, self.onCheck, checkBox)
            self.GetSizer().Add(item=checkBox, pos=(row, col), span=(1, 1))
            if (col == maxColumns):  # last column reached
                row = (row + 1)
                col = 0
            else:  # last column not yet reached
                col = (col + 1)
        self.GetSizer().Layout()



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
    def onCheck(self, observable):
        """User (un)checked a wx.CheckBox. Raise an appropriate wx.EVT_CHECKLISTBOX event
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



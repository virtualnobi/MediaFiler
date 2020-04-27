# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import math
## Contributed
# import wx
#import wx._core
import wx.lib.newevent
## nobi
## Project



# Define wxPython command event 
(CheckBoxGroupEvent, EVT_CHECKBOX_CLICK_IN_GROUP) = wx.lib.newevent.NewCommandEvent()
"""The CheckBoxGroupEvent will provide the following attributes:

String choice contains the label of the checkbox clicked
Number index contains the (0-based) index of the clicked choice in the list of choices
Boolean value contains the state of the checkbox after clicking
"""



class CheckBoxGroup(wx.Panel): 
    """A wx.GridBagSizer containing wx.CheckBoxes, layouted by a wx.GridBagSizer.

    In contrast to wx.CheckListBox, it has a title and allows a grid layout, like a wx.RadioBox.
    So far I have no idea how to put a frame around it like the wx.RadioBox. 

    The EVT_CHECKBOX_CLICK_IN_GROUP event can be bound as usual:

    parentOfCheckBoxGroup.Bind(EVT_CHECKBOX_CLICK_IN_GROUP, handlerFunction)

    The event parameter to handlerFunction will have the following attributes:
    - event.index: Number indicating the index of the checkbox clicked
    - event.choice: String containing the label of the checkbox clicked
    - event.IsChecked(): Boolean indicating the new state of the checkbox clicked
    """
    


# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, 
                 handlerFunction,  # TODO: allow Bind() on CheckBoxGroups and remove this parameter
                 ident=wx.ID_ANY, label='', choices=[], majordimension=0, style=0, 
                 vgap=7, hgap=15,  # similar to wx.RadioBox
                 **kwargs  #pos=(0, 0), size=(0, 0), validator=, name='' 
                 ):
        """
        Create a CheckBoxGroup.
        
        The following styles are supported with the same meaning as in wx.CheckBox():
        wx.CHK_2STATE (default)
        wx.CHK_3STATE
        wx.CHK_ALLOW_3RD_STATE_FOR_USER
        wx.ALIGN_RIGHT
        The following styles are supported with the same meaning as in wx.RadioBox():
        wx.RA_SPECIFY_ROWS
        wx.RA_SPECIFY_COLS (default)

        wx.Window parent: parent window
        Callable handlerFunction: event handler called when checkbox is clicked
        ident: 
        String label: title of checkbox group
        Sequence of String choices: list of checkbox labels
        Number majordimension: number of rows or colummns to use (0 for len(choices))
        Number style: 
        vgap: vertical gap (GridBagSizer parameter)
        hgap: horizontal gap (GridBagSizer parameter)

        RadioBox: label=EmptyString, pos=DefaultPosition, size=DefaultSize, choices=wxPyEmptyStringArray, majorDimension=0, style=RA_HORIZONTAL, validator=DefaultValidator, name=RadioBoxNameStr
        """
        # inheritance
        super(CheckBoxGroup, self).__init__(parent, ident, **kwargs)  # pos, size, style, validator, name)
        # internal state
        self.handlerFunction = handlerFunction
        self.groupLabel = label
        self.labels = choices
        self.checkBoxes = []
        # sizing of the grid
        if (((style & wx.RA_SPECIFY_COLS) == 0)
            and ((style & wx.RA_SPECIFY_ROWS) == 0)):
            style = (style & wx.RA_SPECIFY_COLS) 
        if (style & wx.RA_SPECIFY_COLS):
            if (majordimension == 0):
                self.columnCount = len(choices)
                self.rowCount = 1
            else:
                self.columnCount = majordimension
                self.rowCount = math.floor(len(choices) / majordimension)
        elif (style == wx.RA_SPECIFY_ROWS):
            if (majordimension == 0):
                self.columnCount = 1
                self.rowCount = len(choices)
            else:
                self.columnCount = math.floor(len(choices) / majordimension)
                self.rowCount = majordimension
        #
        gbSizer = wx.GridBagSizer(vgap=vgap, hgap=hgap)
        gbSizer.SetEmptyCellSize((5, 5))  # otherwise, it's (10, 20)
        gbSizer.Add(wx.StaticText(self, -1, self.groupLabel), (0, 0), span=(1, self.columnCount))  # wxPython 4
        col = 0
        row = 1
        for choice in choices:
            checkBox = wx.CheckBox(self, label=choice)
            self.checkBoxes.append(checkBox)
            self.Bind(wx.EVT_CHECKBOX, self.onClick, source=checkBox)
            gbSizer.Add(checkBox,(row, col), span=(1, 1))  # wxPython 4
            col = (col + 1)
            if (col > self.columnCount):  # last column reached
                row = (row + 1)
                col = 0
        hbox = wx.BoxSizer(orient=wx.HORIZONTAL)
        hbox.AddSpacer(5)
        hbox.Add(gbSizer)
        vbox = wx.BoxSizer(orient=wx.VERTICAL)
        vbox.Add(hbox)
        vbox.AddSpacer(5)
        self.SetSizer(vbox)
        gbSizer.Fit(self)
        self.GetSizer().Layout()



# Setters
    def clearAll(self):
        """Unset all checkboxes in self.
        """
        for checkbox in self.checkBoxes:
            checkbox.SetValue(False)



    def setValue(self, indexOrLabel, state, caseSensitive=True):   
        """Set the indicated item in self to the given state.
        
        Number index
        Boolean state
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        self.checkBoxes[index].SetValue(state)
    SetValue = setValue  # provide similar API as CheckBox


    def set3StateValue(self, indexOrLabel, state, caseSensitive=True):
        """Set the indicated item in self to the given state.
        
        Number index
        Boolean state
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        self.checkBoxes[index].Set3StateValue(state)
    Set3ValueValue = set3StateValue  # provide similar API as CheckBox


    def enableItem(self, indexOrLabel, enable=True, caseSensitive=True):
        """Enable the indicated item. 

        Number index: zero-based index of items
        Boolean enable: flag to control enabling vs. disabling
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        self.checkBoxes[index].Enable(enable)
    EnableItem = enableItem  # provide same API as RadioBoxGroup


    def showItem(self, indexOrLabel, show=True, caseSensitive=True):
        """Shows or hides the indicated item in self.

        Number index: zero-based index of items
        Boolean show: flag to control enabling vs. disabling
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        self.checkBoxes[index].Show(show)

        
# Getters
    def getLabel(self):
        """Return the label of the CheckBoxGroup.
        """
        return(self.groupLabel)


    def getCount(self): 
        """Return the number of items in self.
        """
        return(len(self.checkBoxes))

    
    def getRowCount(self): 
        """Return the number of rows in self.
        """
        return(self.rowCount)
    
    
    def getColumnCount(self):  
        """Return the number of columns in self.
        """
        return(self.columnCount)
    

    def is3State(self, indexOrLabel, caseSensitive=True):
        """Return True if the indicated item in self is a 3-state checkbox
        
        Number index: zero-based index of items
        Return Boolean
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        return(self.checkBoxes[index].Is3State())


    def getValue(self, indexOrLabel, caseSensitive=True):  
        """Return the state of the indicated item in self.

        Number index: zero-based index of items
        Return Boolean
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        return(self.checkBoxes[index].GetValue())

    
    def isChecked(self, indexOrLabel, caseSensitive=True):
        """More readable synonym to self.getValue().
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        return(self.getValue(index))


    def findItemLabel(self, label, caseSensitive=True):
        """Return the index of the given label. 
        
        Return Number
        Raises ValueError if label does not exist in self.
        """
        if (caseSensitive):
            index = self.labels.index(label)
            return(index)
        else:
            index = 0
            for boxLabel in self.labels:
                if (self.labels[boxLabel].lower() == label.lower()):
                    return(0)
                index = (index + 1)
            raise ValueError('"%s" not a label in "%s"' % (label, self))
        raise RuntimeError('CheckBoxGroup.findItemLabel() should never reach this statement!')


    def getAllItemLabels(self):
        """Return a Set of all item labels.
        
        Return Set of String
        """
        return[self.labels[i] for i in range(self.getCount())]


    def getItemLabel(self, index):
        """Return the label of the indicated item in self.

        Raises ValueError if index < 0 or self.getCount() < index.

        Number index: zero-based index of items
        Return String
        """
        return(self.labels[index])
    

    def isItemEnabled(self, indexOrLabel, caseSensitive=True):
        """Return True if the indicated item in self is enabled, False otherwise.

        Number index: zero-based index of items
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        return(self.checkBoxes[index].IsEnabled())


    def isItemShown(self, indexOrLabel, caseSensitive=True):
        """Return True if the indicated item is shown.
        
        Number index: zero-based index of items
        Return Boolean
        Raises ValueError or TypeError
        """
        index = self.ensureNumericIndex(indexOrLabel, caseSensitive)
        return(self.checkBoxes[index].IsShown())



# Event Handlers
    def onClick(self, event):
        """User clicked a wx.CheckBox. 
        """
        checkbox = event.GetEventObject()
        index = self.checkBoxes.index(checkbox)
        choice = self.labels[index][:]  # deep copy to be thread-safe in wx.ProcessEvent()
        newEvent = CheckBoxGroupEvent(0,  # wxPython 4 
                                      index=index, 
                                      choice=choice,
                                      value=checkbox.IsChecked())
#        newEvent.__setattr__('EventObject', self) 
        newEvent.SetEventObject(self)  # wxPython 4
        wx.PostEvent(self.GetParent(), newEvent)  # TODO: after migrating to wxPython 4, use QueueEvent() for thread safety



# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
    def ensureNumericIndex(self, indexOrLabel, caseSensitive=True):
        """Return a numeric index into self, regardless of type of indexOrLabel. 
        
        Used in all API functions which accept a numeric or string index, handling conversion and
        error handling. 
        
        Return Number
        Raises TypeError or ValueError
        """
        if (isinstance(indexOrLabel, str)):
            index = self.findItemLabel(indexOrLabel, caseSensitive)
        elif (isinstance(indexOrLabel, int)):
            if ((0 <= indexOrLabel) 
                and (indexOrLabel <= self.getCount())):
                index = indexOrLabel
            else:
                raise ValueError('Numeric index out of range!')
        else:
            raise TypeError('First parameter can only be int or str!')
        return(index)

        
# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



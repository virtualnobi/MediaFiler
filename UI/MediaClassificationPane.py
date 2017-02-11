# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## standard
import os.path
import gettext
## contributed
import wx.lib.scrolledpanel
import wx.lib.rcsizer
## nobi
from ObserverPattern import Observable, Observer
#from wxExtensions.CheckBoxGroup import CheckBoxGroup
## project
import UI
from Model.Entry import Entry



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



class MediaClassificationPane(wx.lib.scrolledpanel.ScrolledPanel, Observer, Observable):
    """To displays the classification of the currently selected Entry.

    It observes the ImageFilerModel for selection changes, and the selected Entry for name changes.

    Observable aspects:
    'classification': the classification has been changed by the user
    """


# Constants
    ClassDontChangeText = _('(n/a)')
    ClassDontChangeIndex = 0
    ClassUnselectedText = _('(none)')
    ClassUnselectedIndex = 1



# Class Variables
# Class Methods
# Lifecycle
    def __init__ (self, parent, style=0):
        """Create a new instance inside a given window.

        wx.Window parent is the mebedding window
        """
        # inheritance
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, size=wx.Size (450, 0), style=(style | wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        Observable.__init__(self, ['classification'])
        # 
        self.SetAutoLayout(1)
        self.SetupScrolling()
        # init variables
        self.model = None  # for definition of selectionBoxes
        self.entry = None  # for selecting selectionBoxes
        self.selectionBoxes = {}  # selectionBoxes (as className->RadioBox mapping)
        # vertical sizer for entire pane
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))



# Getters
    def getClassification(self):
        """Return the current classification.
        
        Classes for which "n/a" is selected do not appear in the result.
        Classes for which "(none)" is selected appear in the result with an empty string as element.
        All other classes appear in the result with the selected element. 
        
        Returns a Dictionary mapping Strings to Arrays of Strings, mapping class names to lists of elements.
        """
        result = {}
        for className in self.model.getClassHandler().getClassNames():
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes used
                elements = []
                for choice in self.selectionBoxes[className]['list']:
                    if (choice.IsChecked()):
                        elements.append(choice.GetLabel())
                if (0 < len(elements)):
                    result[className] = elements
            else:  # single selection, radioboxes used
                if (self.selectionBoxes[className].GetSelection() == self.ClassDontChangeIndex): 
                    pass
                elif (self.selectionBoxes[className].GetSelection() == self.ClassUnselectedIndex):  
                    result[className] = []
                else:  # real element name
                    result[className] = [self.selectionBoxes[className].GetStringSelection()]
        return(result)



# Setters
    def setModel(self, imageFilerModel):
        """Set the model, and create widgets on self accordingly.
        """
        if (self.model):
            self.clear()
            self.model.removeObserver(self)
        self.model = imageFilerModel
        self.model.addObserverForAspect(self, 'selection')
        # store references to selectionBoxes here
        self.selectionBoxes = {}
        # create content
        classNames = self.model.getClassHandler().getClassNames()
        for className in classNames:
            # choices contain 'n/a' for "Don't change (for groups)" and '' for "None applies", plus class elements
            choices = [self.ClassDontChangeText, self.ClassUnselectedText]
            choices.extend(self.model.getClassHandler().getElementsOfClassByName(className))
            # determine columns for selectionBoxes/checkboxes
            def longest(length, item): 
                if (length < len(item)):
                    return(len(item))
                else:
                    return(length)
            maxChoiceLength = reduce(longest, choices, 0)
            if (maxChoiceLength < 10):
                columns = min (len (choices), 5)
            else:
                columns = min (len (choices), 4)
            # create radiobox/checkbox group with class elements
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, use checkboxes
                choices.remove('(none)')  # not needed for checkboxes
                # data container for checkboxes and Sizer
                checkboxes = dict()
                checkboxes['list'] = []
                checkboxes['sizer'] = wx.lib.rcsizer.RowColSizer()  # TODO: switch to GridBagSizer; it's newer
#                checkboxes['sizer'] = wx.GridBagSizer(round(len(choices)/columns), columns)
                # create all checkboxes within the sizer
                checkBoxSizer = checkboxes['sizer']
                checkBoxSizer.Add(item=wx.StaticText(self, -1, className), row=0, col=1, colspan=columns)  # TODO: switch to GridBagSizer; it's newer
                row = 1
                col = 1
                for choice in choices: 
                    # add a checkbox
                    checkBox = wx.CheckBox(self, -1, choice)
                    self.Bind(wx.EVT_CHECKBOX, self.onSelect, checkBox)  # attach event
                    checkboxes['list'].append(checkBox)
                    checkBoxSizer.Add(item=checkBox, row=row, col=col)  # TODO: switch to GridBagSizer; it's newer
                    # determine position of next checkbox
                    if (col == columns):  # last column reached
                        row = (row + 1)
                        col = 1
                    else:  # last column not yet reached
                        col = (col + 1)
                # store checkboxes
                self.selectionBoxes[className] = checkboxes
                # put checkbox sizer into layout
                self.GetSizer().Add(checkBoxSizer)
                # add new CheckBoxGroup
# TODO:                self.GetSizer().Add(CheckBoxGroup(self, label=className, choices=choices))
            else:  # single selection, use selectionBoxes
                radioBox = wx.RadioBox (self, 
                                        -1, 
                                        label=className, 
                                        choices=choices, 
                                        majorDimension=columns,
                                        style=(wx.RA_HORIZONTAL | wx.RA_SPECIFY_COLS))
                self.Bind (wx.EVT_RADIOBOX, self.onSelect, radioBox)  # attach event
                # store radiobox 
                self.selectionBoxes[className] = radioBox
                # put radiobox into layout
                self.GetSizer().Add(radioBox)
        # after all selectionBoxes are added, ensure scrolling works
        self.SetupScrolling()


    def clear(self):
        """Remove all widgets from self.
        """
        # remove all selectionBoxes if there are any
        for className in self.selectionBoxes.keys():
            # TODO: self.Unbind(event, source, id, id2, handler)
            container = self.selectionBoxes[className]
            if (self.model.getClassHandler().isMultipleClassByName(className)):
                self.GetSizer().Remove(container['sizer'])
            else:
                self.GetSizer().Remove(container) # not self.RemoveChild(container)

    
    def setEntry (self, entry):
        """Set the selected entry (either group or image), and enable/set checkboxes and radiobuttons accordingly.
        """
        # observer pattern
        if (self.entry):
            self.entry.removeObserver(self)  # unregister from previous observable
        self.entry = entry
        if (entry == None):
            pass
        self.entry.addObserverForAspect(self, 'name')  # register for changes of name
        # enable the first radiobutton in each group (the 'n/a' one) only if entry is a group
        for className in self.model.getClassHandler().getClassNames():
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, use checkboxes
                self.selectionBoxes[className]['list'][0].Enable(self.entry.isGroup())
            else:  # single selection, use radiobuttons
                self.selectionBoxes[className].EnableItem(0, self.entry.isGroup())
        # fill in data from the selected entry/group
        entryElements = self.entry.getKnownElements()
        for className in self.model.getClassHandler().getClassNames():
            hits = entryElements.intersection(self.model.getClassHandler().getElementsOfClassByName(className))
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes
                for checkBox in self.selectionBoxes[className]['list']:  # translate each existing class element into checked box 
                    checkBox.SetValue(checkBox.GetLabel() in hits)
            else:  # single selection, radioboxes
                if (len(hits) > 0):  # applies, select radio button
                    self.selectionBoxes[className].SetStringSelection(hits.pop())
                else:  # does not apply
                    if (self.entry.isGroup()):  # for a group, select "n/a" item
                        self.selectionBoxes[className].SetSelection(0)
                    else:  # for an image, select empty item
                        self.selectionBoxes[className].SetSelection(1)
        # relayout
        self.SetupScrolling()
        self.GetSizer().Layout()



# Event Handlers
    def onSelect (self, event):  # @UnusedVariable
        """User changed selection.
        """
        classMapping = self.getClassification()
        elements = set()
        for className in classMapping:
            for element in classMapping[className]:
                elements.add(element)
        elements.update(self.entry.getUnknownElements())
        self.entry.renameTo(elements=elements)
        


# Inheritance - ObserverPattern
    def updateAspect(self, observable, aspect):
        """ASPECT of OBSERVABLE has changed. 
        """
        super(MediaClassificationPane, self).updateAspect (observable, aspect)
        if (aspect == 'selection'):
            self.setEntry(observable.getSelectedEntry())
        if (aspect == 'name'):
            self.setEntry(observable)
        


# Internal
    def currentFilename (self):
        # Return the file name of entry as defined by current radiobox selections
        result = ''
        classification = self.getClassification()
        for className in self.model.getClassHandler().getClassNames():
            if className in classification.keys():
                for element in classification[className]:
                    result = (result + Entry.NameSeparator + element)
        for element in self.entry.getUnknownElements ():
            result = (result + '.' + element)
        return (result)



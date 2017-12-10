# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## standard
import os.path
import gettext
import logging
## contributed
import wx.lib.scrolledpanel
## nobi
from nobi.ObserverPattern import Observer
from nobi.wx.CheckBoxGroup import CheckBoxGroup, EVT_CHECKBOX_CLICK_IN_GROUP, CheckBoxGroupEvent
## project
import UI
# from Model.Entry import Entry
# from Model.MediaClassHandler import MediaClassHandler



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at %s; using originals instead of %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message



class MediaClassificationPane(wx.lib.scrolledpanel.ScrolledPanel, Observer):
    """To display the classification of the currently selected Entry.

    It observes the ImageFilerModel for selection changes, and the selected Entry for name changes.
    """


# Constants
    ClassDontChangeText = _('(n/a)')
    ClassDontChangeIndex = 0
    ClassUnselectedText = _('(none)')
    ClassUnselectedIndex = 1



# Class Variables
    Logger = logging.getLogger(__name__)



# Class Methods
# Lifecycle
    def __init__ (self, parent, style=0):
        """Create a new instance inside a given window.

        wx.Window parent is the embedding window
        """
        # inheritance
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, size=wx.Size(450, 0), style=(style | wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        # init variables
        self.model = None  # for definition of selectionBoxes
        self.entry = None  # for selecting selectionBoxes
        self.selectionBoxes = {}  # selectionBoxes (as className->RadioBox/CheckBoxGroup mapping)
        # vertical sizer for entire pane
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        # 
        self.SetAutoLayout(1)
        self.SetupScrolling()


    def setModel(self, mediaCollection):
        """Set the model, and create widgets on self accordingly.
        """
        # observe model
        if (self.model):
            self.clear()
            self.model.removeObserver(self)
        self.model = mediaCollection
        self.model.addObserverForAspect(self, 'selection')
        # add widgets
        self.selectionBoxes = {}
        for className in self.model.getClassHandler().getClassNames():
            # choices contain "Don't change" (for groups) and "None applies", plus class elements
            choices = [self.ClassDontChangeText, self.ClassUnselectedText]
            choices.extend(self.model.getClassHandler().getElementsOfClassByName(className))
            # determine columns for selectionBoxes/checkboxes
            def longest(length, item): 
                if (length < len(item)):
                    return(len(item))
                else:
                    return(length)
            maxChoiceLength = reduce(longest, choices, 0)
            if (maxChoiceLength < 7):
                columns = min(len(choices), 5)
            else:
                columns = min(len(choices), 4)
            # create radiobox/checkbox group with class elements
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, use checkboxes
                choices.remove(self.__class__.ClassUnselectedText)  # not needed for checkboxes
                # add new CheckBoxGroup
                checkBox = CheckBoxGroup(self, 
                                         self.onSelect, 
                                         label=className,
                                         majordimension=columns,
                                         style=wx.RA_SPECIFY_COLS, 
                                         choices=choices)
                self.Bind(EVT_CHECKBOX_CLICK_IN_GROUP, self.onSelect)
                self.GetSizer().Add(checkBox)
                # store checkboxes
                self.selectionBoxes[className] = checkBox
            else:  # single selection, use selectionBoxes
                radioBox = wx.RadioBox(self, 
                                       -1, 
                                       label=className, 
                                       choices=choices, 
                                       majorDimension=columns,
                                       style=(wx.RA_HORIZONTAL | wx.RA_SPECIFY_COLS))
                self.Bind(wx.EVT_RADIOBOX, self.onSelect, radioBox)  # attach event
                # store radiobox 
                self.selectionBoxes[className] = radioBox
                # put radiobox into layout
                self.GetSizer().Add(radioBox)
        # after all selectionBoxes are added, ensure scrolling works
        self.SetupScrolling()
        self.setEntry(self.model.getSelectedEntry())



# Getters
    def getClassification(self):
        """Return the current classification, mapping class names to lists of elements.
        
        Classes for which "n/a" is selected do not appear in the result.
        Classes for which "(none)" is selected appear in the result with an empty string as element.
        All other classes appear in the result with the selected element. 
        
        Returns a Dictionary mapping Strings to Arrays of Strings.
        """
        result = {}
        for className in self.model.getClassHandler().getClassNames():
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes used
                elements = []
                for element in self.model.getClassHandler().getElementsOfClassByName(className):
                    if (self.selectionBoxes[className].isChecked(element)):  
                        elements.append(element)
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
    def setEntry (self, entry):
        """Set the selected entry (either group or image), and enable/set checkboxes and radiobuttons accordingly.
        """
        self.__class__.Logger.debug('MediaClassificationPane.setEntry(%s)' % entry.getPath())
        # observer pattern
        if (self.entry):
            self.entry.removeObserver(self)  # unregister from previous observable
        self.entry = entry
        if (self.entry == None):
            self.clear()
            return 
        self.entry.addObserverForAspect(self, 'name')
        # 
        entryElements = self.entry.getKnownElements()
        for className in self.model.getClassHandler().getClassNames():
            selectionBox = self.selectionBoxes[className]
            # enable first button in each group (the 'n/a' one) only if entry is a group
            selectionBox.EnableItem(self.__class__.ClassDontChangeIndex, self.entry.isGroup())
            # fill in data from the selected entry/group
            hits = entryElements.intersection(self.model.getClassHandler().getElementsOfClassByName(className))
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes
                selectionBox.clearAll() 
                if (len(hits) == 0):  # no tag of this class selected
                    if (self.entry.isGroup()):
                        selectionBox.setValue(self.__class__.ClassDontChangeIndex, True)
                else:  # tag(s) of this class selected
                    for element in self.model.getClassHandler().getElementsOfClassByName(className):
                        selectionBox.setValue(element, (element in hits))
            else:  # single selection, radioboxes
                if (len(hits) == 0):  # no tag of this class selected
                    if (self.entry.isGroup()):  # for a group, select "n/a" item
                        selectionBox.SetSelection(self.__class__.ClassDontChangeIndex)
                    else:  # for an image, select empty item
                        selectionBox.SetSelection(self.__class__.ClassUnselectedIndex)
                else:  # tag of this class selected
                    selectionBox.SetStringSelection(hits.pop())
        # relayout
        self.SetupScrolling()
        self.GetSizer().Layout()



# Event Handlers
    def onSelect (self, event):  # @UnusedVariable
        """User changed selection.
        """
        if (isinstance(event, CheckBoxGroupEvent)):
            checkBoxGroup = event.GetEventObject()
            if (checkBoxGroup.isChecked(self.__class__.ClassDontChangeIndex)
                and (event.index <> self.__class__.ClassDontChangeIndex)
                and (event.value == True)):
                checkBoxGroup.setValue(self.__class__.ClassDontChangeIndex, False)
            elif (checkBoxGroup.isChecked(self.__class__.ClassDontChangeIndex)
                  and (event.index == self.__class__.ClassDontChangeIndex)):
                checkBoxGroup.clearAll()
                checkBoxGroup.setValue(self.__class__.ClassDontChangeIndex, True)
        classMapping = self.getClassification()
        elements = set()
        for className in classMapping:
            for element in classMapping[className]:
                elements.add(element)
        elements.update(self.entry.getUnknownElements())
        self.entry.renameTo(elements=elements)  # TODO: allow to remove classes from groups



# Inheritance - ObserverPattern
    def updateAspect(self, observable, aspect):
        """ASPECT of OBSERVABLE has changed. 
        """
        super(MediaClassificationPane, self).updateAspect (observable, aspect)
        if (aspect == 'selection'):
            self.setEntry(observable.getSelectedEntry())
        elif (aspect == 'name'):
            self.setEntry(observable)



# Internal
    def clear(self):
        """Remove all widgets from self.
        """
        # remove all selectionBoxes if there are any
        for className in self.selectionBoxes.keys():
            container = self.selectionBoxes[className]
            self.GetSizer().Remove(container)  # not self.RemoveChild(container)
        self.selectionBoxes = {}
        while (0 < len(self.GetSizer().GetChildren())):
            self.GetSizer().Remove(0)
        self.DestroyChildren()

    

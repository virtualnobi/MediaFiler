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



# Package Variables
Logger = logging.getLogger(__name__)



class MediaClassificationPane(wx.lib.scrolledpanel.ScrolledPanel, Observer):
    """To display the classification of the currently selected Entry.

    It observes the ImageFilerModel for selection changes, and the selected Entry for name changes.
    """


# Constants
    ClassDontChangeText = _('(no change)')
    ClassDontChangeIndex = 0
    ClassUnselectedText = _('(none)')
    ClassUnselectedIndex = 1



# Class Variables
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
                choices.remove(MediaClassificationPane.ClassUnselectedText)  # not needed for checkboxes
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
# Setters
    def setEntry (self, entry):
        """Set the selected entry (either group or image), and enable/set checkboxes and radiobuttons accordingly.
        """
        Logger.debug('MediaClassificationPane.setEntry(%s)' % entry.getPath())
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
        self.setTags(entryElements)
#         for className in self.model.getClassHandler().getClassNames():
#             selectionBox = self.selectionBoxes[className]
#             # enable first button in each group (the 'n/a' one) only if entry is a group
#             selectionBox.EnableItem(MediaClassificationPane.ClassDontChangeIndex, self.entry.isGroup())
#             # fill in data from the selected entry/group
#             hits = entryElements.intersection(self.model.getClassHandler().getElementsOfClassByName(className))
#             if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes
#                 selectionBox.clearAll() 
#                 if (len(hits) == 0):  # no tag of this class selected
#                     if (self.entry.isGroup()):
#                         selectionBox.setValue(MediaClassificationPane.ClassDontChangeIndex, True)
#                 else:  # tag(s) of this class selected
#                     for element in self.model.getClassHandler().getElementsOfClassByName(className):
#                         selectionBox.setValue(element, (element in hits))
#             else:  # single selection, radioboxes
#                 if (len(hits) == 0):  # no tag of this class selected
#                     if (self.entry.isGroup()):  # for a group, select "n/a" item
#                         selectionBox.SetSelection(MediaClassificationPane.ClassDontChangeIndex)
#                     else:  # for an image, select empty item
#                         selectionBox.SetSelection(MediaClassificationPane.ClassUnselectedIndex)
#                 else:  # tag of this class selected
#                     selectionBox.SetStringSelection(hits.pop())
#         # relayout
#         self.SetupScrolling()
#         self.GetSizer().Layout()


    def setTags(self, tagSet):
        """Set self's radio and check boxes according to tag set
        
        Set of String tagSet
        """
        for className in self.model.getClassHandler().getClassNames():
            selectionBox = self.selectionBoxes[className]
            # enable first button in each group (the 'n/a' one) only if entry is a group
            selectionBox.EnableItem(MediaClassificationPane.ClassDontChangeIndex, self.entry.isGroup())
            # fill in data from the selected entry/group
            hits = tagSet.intersection(self.model.getClassHandler().getElementsOfClassByName(className))
            if (self.model.getClassHandler().isMultipleClassByName(className)):  # multiple selection, checkboxes
                selectionBox.clearAll() 
                if (len(hits) == 0):  # no tag of this class selected
                    if (self.entry.isGroup()):
                        selectionBox.setValue(MediaClassificationPane.ClassDontChangeIndex, True)
                else:  # tag(s) of this class selected
                    for element in self.model.getClassHandler().getElementsOfClassByName(className):
                        selectionBox.setValue(element, (element in hits))
            else:  # single selection, radioboxes
                if (len(hits) == 0):  # no tag of this class selected
                    if (self.entry.isGroup()):  # for a group, select "n/a" item
                        selectionBox.SetSelection(MediaClassificationPane.ClassDontChangeIndex)
                    else:  # for an image, select empty item
                        selectionBox.SetSelection(MediaClassificationPane.ClassUnselectedIndex)
                else:  # tag of this class selected
                    selectionBox.SetStringSelection(hits.pop())

        

# Event Handlers
    def onSelect (self, event):  # @UnusedVariable
        """User changed selection.
        
        Let all options be active, and adapt depending options according to user's change. 
        """
        change = ''
        groupBox = event.GetEventObject()
        className = None
        for className in self.selectionBoxes: 
            if (groupBox == self.selectionBoxes[className]):
                break
        if (className == None):
            Logger.warning('MediaClassificationPane.onSelect(): Did not find selected group %s' % groupBox)
        # determine which tag is removed and which one added
        if (isinstance(event, CheckBoxGroupEvent)):
            if (groupBox.isChecked(MediaClassificationPane.ClassDontChangeIndex)
                and (event.index <> MediaClassificationPane.ClassDontChangeIndex)
                and (event.value == True)):
                addedTag = groupBox.getItemLabel(event.index)
                removedTags = set()
                groupBox.setValue(MediaClassificationPane.ClassDontChangeIndex, False)
                change = ('added tag %s in check group "%s"' % (addedTag, className))
            elif (groupBox.isChecked(MediaClassificationPane.ClassDontChangeIndex)
                  and (event.index == MediaClassificationPane.ClassDontChangeIndex)):
                addedTag = None
                removedTags = [tag for tag in groupBox.getAllItemLabels() if groupBox.isItemEnabled(tag)]
                groupBox.clearAll()
                groupBox.setValue(MediaClassificationPane.ClassDontChangeIndex, True)
                change = ('removed tags from check group "%s"' % className)
            else:  # regular tag in a CheckBoxGroup
                if (event.value):
                    addedTag = groupBox.getItemLabel(event.index)
                    removedTags = set()
                else:
                    addedTag = None
                    removedTags = set([groupBox.getItemLabel(event.index)])
                change = ('%s tag "%s" in check group "%s"' % (('added' if event.value else 'removed'), 
                                                           groupBox.getItemLabel(event.index),
                                                           className))
        else:  # RadioBox event
            if (groupBox.GetSelection() == MediaClassificationPane.ClassDontChangeIndex):
                addedTag = None
            elif (groupBox.GetSelection() == MediaClassificationPane.ClassUnselectedIndex):
                addedTag = None
            else:  # real tag selected
                addedTag = groupBox.GetItemLabel(groupBox.GetSelection())
            removedTags = (self.entry.getKnownElements() - self.getTags())
            change = ('changed to tag %s in radio group %s' % (addedTag, 
                                                               className))
        Logger.debug('MediaClassificationPane.onSelect(): %s' % change)
        Logger.debug('MediaClassificationPane.onSelect(): added "%s", removed %s' % (addedTag, removedTags))
        classesToRemove = self.getClassesToRemove()  # store before self.setTags()
        # adapt other tags as needed
        elements = self.model.getClassHandler().getTagsOnChange(self.entry.getKnownElements(), addedTag, removedTags)
        self.setTags(elements)
        elements.update(self.entry.getUnknownElements())
        # change media pathname
        pathInfo = self.entry.getOrganizer().getPathInfo()
        pathInfo['elements'] = elements
        pathInfo['classesToRemove'] = classesToRemove
        self.entry.renameTo(**pathInfo)



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


    def getTags(self):
        """Return the set of all tags to be assigned to the current Entry.
        
        Return Set of String
        """
        result = set()
        for className in self.selectionBoxes:
            if (self.model.getClassHandler().isMultipleClassByName(className)):
                checkBoxGroup = self.selectionBoxes[className]
                for tag in self.model.getClassHandler().getElementsOfClassByName(className):
                    if (checkBoxGroup.isChecked(tag)):
                        result.add(tag)
            else:
                radioBoxGroup = self.selectionBoxes[className]
                if ((radioBoxGroup.GetSelection() <> self.ClassDontChangeIndex)
                    and (radioBoxGroup.GetSelection() <> self.ClassUnselectedIndex)):
                    result.add(radioBoxGroup.GetStringSelection())
        return(result)


    def getClassesToRemove(self):
        """Return the set of classes whose tags shall be removed from the current Entry.
        
        Return Set of String
        """
        result = set()
        for className in self.selectionBoxes:
            if (self.model.getClassHandler().isMultipleClassByName(className)):
                pass
            else:
                if (self.selectionBoxes[className].GetSelection() == MediaClassificationPane.ClassUnselectedIndex):
                    result.add(className)
        return(result)



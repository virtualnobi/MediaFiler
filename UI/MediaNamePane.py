#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""

# Imports
## standard
import logging
import sys
## contributed
import wx
## nobi
from nobi.ObserverPattern import Observer
## project
from UI import GUIId
#from Model.Entry import Entry



class MediaNamePane(wx.Panel, Observer):
    """Panel displaying the file name components of the currently selected Entry. 
    
    Asks the model's organizationStrategy to add the fields relevant to the organization. 
    
    Observes the MediaCollection model for changes of selection, 
    and the Entry for changes of name.
    """
# Constants
    RenameImage = wx.NewId()  # identifier of "Rename" button
    ReuseLastElements = wx.NewId()  # identifer of "Reuse Last" button



# Class Methods    
# Lifecycle
    def __init__(self, parent, style=0):
        """Create a new pane to show and enter media names.
        
        wx.Window parent is the parent window to display the new pane
        """
        # inheritance
        wx.Panel.__init__(self, parent, style=(style | wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        # internal state
        self.model = None
        self.entry = None
        self.lastKnownElements = set()  # to assign the elements used last time again
        self.lastUnknownElements = set()  # to assign the elements used last time again
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))



# Setters
    def setModel(self, aMediaCollection):
        """Set the model and derive the identification fields from it.
        """
        #print('MediaNamePane.setModel()')
        # establish observer relation
        if (self.model):
            self.model.removeObserver(self)            
            while (len(self.GetSizer().GetChildren()) > 0):
                self.GetSizer().Remove(0)
            self.DestroyChildren()
        self.model = aMediaCollection
        self.model.addObserverForAspect(self, 'selection')
        # create child controls
        self.model.organizationStrategy.initNamePane(self)
        # elements
        self.elementInput = wx.TextCtrl (self, style=wx.TE_PROCESS_ENTER)
        self.elementInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
        self.GetSizer().Add(self.elementInput, proportion=1, flag=(wx.EXPAND | wx.ALIGN_CENTER_VERTICAL))
        # Rename button
        self.renameButton = wx.Button (self, id=GUIId.RenameMedia, label=GUIId.FunctionNames[GUIId.RenameMedia])
        self.renameButton.Bind (wx.EVT_BUTTON, self.onRename, id=GUIId.RenameMedia)
        self.GetSizer().Add (self.renameButton, flag=(wx.ALIGN_CENTER_VERTICAL))
        # Reuse button
        self.reuseButton = wx.Button(self, id=GUIId.ReuseLastClassification, label=GUIId.FunctionNames[GUIId.ReuseLastClassification])
        self.reuseButton.Bind(wx.EVT_BUTTON, self.onReuseLastClasses, id=GUIId.ReuseLastClassification)
        self.GetSizer().Add(self.reuseButton, flag=(wx.ALIGN_CENTER_VERTICAL))        
        # Legalize button
        self.legalizeButton = wx.Button(self, id=GUIId.RemoveIllegalElements, label=GUIId.FunctionNames[GUIId.RemoveIllegalElements])
        self.legalizeButton.Bind(wx.EVT_BUTTON, self.onLegalize, id=GUIId.RemoveIllegalElements)
        self.GetSizer().Add(self.legalizeButton, flag=(wx.ALIGN_CENTER_VERTICAL))
        # filesize 
        self.sizeString = wx.StaticText(self, -1, '')
        self.GetSizer().Add(self.sizeString, border=50, flag=(wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT))
        # 
        self.setEntry(self.model.getSelectedEntry())
        self.GetSizer().Layout()


    def setEntry(self, entry):
        """Show the name elements of the selected entry.
        
        Model.Entry entry
        """
        logging.debug('MediaNamePane.setEntry(%s)' % entry.getPath())
        # establish observer relation
        if (self.entry):
            self.entry.removeObserver(self)
        self.entry = entry
        self.entry.addObserverForAspect(self, 'name')
        # internal state
        if (entry <> self.model.root):
            self.entry.organizer.setValuesInNamePane(self)
            self.knownElements = entry.getKnownElements()
            self.unknownElements = entry.getUnknownElements()
            self.setElementField()
            self.sizeString.SetLabel(self.entry.getSizeString())
        self.GetSizer().Layout()


# Getters
# Event Handlers
    def onLegalize(self, event):  # @UnusedVariable
        """User wants to remove all illegal elements from image name. 
        
        Save the classification for later re-use.
        """
        self.renameEntry(removeUnknownTags=True)


    def onReuseLastClasses (self, event):  # @UnusedVariable
        """User wants to assign the same classes as used in last class assignment.
        """
        elementString = self.model.getClassHandler().elementsToString(self.lastKnownElements.union(self.lastUnknownElements))
        self.elementInput.ChangeValue(elementString)
        self.renameEntry(removeUnknownTags=False)


    def onRename(self, event):  # @UnusedVariable
        """User wants to rename the entry to values on UI. 
        
        Save the classification for later re-use.
        """
        self.renameEntry(removeUnknownTags=False)



# Inheritance - ObserverPattern
    def updateAspect(self, observable, aspect):
        """ ASPECT of OBSERVABLE has changed. 
        """
        #print('MediaNamePane: Received change of aspect "%s" of "%s"' % (aspect, observable))
        super(MediaNamePane, self).updateAspect(observable, aspect)
        if (aspect == 'selection'):
            entry = observable.getSelectedEntry()
            self.setEntry(entry)
        elif (aspect == 'name'):  # the selected Entry's name has changed
            self.entry.organizer.setValuesInNamePane(self)
            self.knownElements = self.entry.getKnownElements()
            self.unknownElements = self.entry.getUnknownElements()
            self.setElementField()
            self.rememberElements()


# Other API Functions
# Internal
    def setElementField(self):
        """Set value of tag input field from selected entry.
        """
        knownTags = self.entry.getKnownElements()
        unknownTags= self.entry.getUnknownElements()
        elementString = self.model.getClassHandler().elementsToString(knownTags.union(unknownTags))
        self.elementInput.ChangeValue(elementString)

        
    def rememberElements(self):
        """Store tags from selected entry, for re-use. 
        """
        self.lastKnownElements = self.entry.getKnownElements()
        self.lastUnknownElements = self.entry.getUnknownElements()
        logging.debug('MediaNamePane.rememberElements(): Saved "%s" and "%s"' % (self.lastKnownElements, self.lastUnknownElements))


    def renameEntry(self, removeUnknownTags=False):
        """Rename the entry to the identifier and tags given in the input fields.

        If removeUnknownTags=False, the elements given in the tags input field are taken into account. 
        If removeUnknownTags=True, only illegal elements are removed, and the tags input field is ignored.

        Boolean removeUnknownTags indicates whether unknown tags shall be cleared from entry
        """
        pathInfo = self.entry.organizer.getValuesFromNamePane(self)
        if (removeUnknownTags == False):
            tagString = self.elementInput.GetValue()
            tagString = unicode(tagString).encode(sys.getfilesystemencoding(), 'replace')
            tagSet = self.model.getClassHandler().stringToElements(tagString)
            pathInfo['elements'] = tagSet 
        pathInfo['removeIllegalElements'] = removeUnknownTags
        success = self.entry.renameTo(**pathInfo)
        if (success):
            self.model.setSelectedEntry(self.entry)  # when switching groups, old parent group will change selection to itself 
            self.rememberElements()
        else:
            dlg = wx.MessageDialog(self,   # TODO: add error message to Dialog
                                   'Cannot rename media!',
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()


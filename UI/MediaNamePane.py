#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""

# Imports
## standard
import logging
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
        if (self.model):
            self.model.removeObserver(self)            
            while (len(self.GetSizer().GetChildren()) > 0):
                self.GetSizer().Remove(0)
            self.DestroyChildren()
        self.model = aMediaCollection
        self.model.addObserverForAspect(self, 'selection')
        # padding item
        self.GetSizer().Add(wx.StaticText(self, -1, '  '))
        # depending on model organization, change fields for identification
        if (self.model.organizedByDate):
            pass
#             # year
#             self.yearInput = wx.TextCtrl (self, size=wx.Size(80,-1), style=wx.TE_PROCESS_ENTER)
#             self.yearInput.Enable(True)
#             self.yearInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.yearInput, flag=(wx.ALIGN_CENTER_VERTICAL))
#             # padding item
#             self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
#             # month
#             self.monthInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
#             self.monthInput.Enable(True)
#             self.monthInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.monthInput, flag=(wx.ALIGN_CENTER_VERTICAL))
#             # padding item
#             self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
#             # day
#             self.dayInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
#             self.dayInput.Enable(True)
#             self.dayInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.dayInput, flag=(wx.ALIGN_CENTER_VERTICAL))
#             # padding item
#             self.GetSizer().Add(wx.StaticText(self, -1, '/'), flag=(wx.ALIGN_CENTER_VERTICAL))
#             # number
#             self.numberInput = wx.TextCtrl (self, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
#             self.numberInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        else:  # organized by name
            pass
#             # name
#             self.identifierString = wx.StaticText(self, -1, 'none')
#             self.GetSizer().Add(self.identifierString, flag = (wx.ALIGN_CENTER_VERTICAL))
#             # padding item
#             self.GetSizer().Add(wx.StaticText(self, -1, '/'), flag=(wx.ALIGN_CENTER_VERTICAL))
#             # scene 
#             self.sceneInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
#             self.sceneInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.sceneInput, flag=(wx.ALIGN_CENTER_VERTICAL))
#             # padding item
#             self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
#             # number
#             self.numberInput = wx.TextCtrl (self, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
#             self.numberInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
#             self.GetSizer().Add(self.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # number
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
        # establish observer pattern
#        self.clear()
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
#            self.setInputFields()
        self.GetSizer().Layout()


# Getters
# Event Handlers
    def onLegalize(self, event):  # @UnusedVariable
        """User wants to remove all illegal elements from image name. 
        
        Save the classification for later re-use.
        """
#         self.readInputFields()  # ensure all other changes to input fields are kept
#         self.unknownElements = set()  # remove unknown elements 
#         self.lastKnownElements = self.knownElements
#         self.lastUnknownElements = self.unknownElements
        self.renameEntry(removeUnknownTags=True)


    def onReuseLastClasses (self, event):  # @UnusedVariable
        """User wants to assign the same classes as used in last class assignment.
        """
#         self.readInputFields()  # ensure all other changes to input fields are kept
#         self.knownElements = self.lastKnownElements
#         self.unknownElements = self.lastUnknownElements
#         self.setInputFields()
        elementString = self.model.getClassHandler().elementsToString(self.lastKnownElements.union(self.lastUnknownElements))
        self.elementInput.ChangeValue(elementString)
        self.renameEntry(removeUnknownTags=False)


    def onRename(self, event):  # @UnusedVariable
        """User wants to rename the entry to values on UI. 
        
        Save the classification for later re-use.
        """
#         self.readInputFields()
#         self.lastKnownElements = self.knownElements
#         self.lastUnknownElements = self.unknownElements
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

        Boolean removeUnknownTags indicates whether unknown tags shall be cleared from entry
        """
        pathInfo = self.entry.organizer.getValuesFromNamePane(self)
        tagString = self.elementInput.GetValue()
        tagSet = self.model.getClassHandler().stringToElements(tagString)
        pathInfo['elements'] = tagSet  # (self.knownElements.union(self.unknownElements))
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


# 
#     
#     def clear(self):
#         """Clear all fields, since no Entry is selected
#         """
#         # clean up OberverPattern
#         if (self.entry):  
#             self.entry.removeObserver(self)  # unregister from previous observable
#         self.entry = None
#         # clear internal components
#         if (self.model.organizedByDate):
#             self.year = u''
#             self.month = u''
#             self.day = u''
#         else:
#             self.name = u''
#             self.scene = u''
#         self.number = u''
#         self.knownElements = set()
#         self.unknownElements = set()
#         # display component values
#         self.setInputFields()
# 
# 
#     def setInputFields(self):
#         """Set input fields from internal state.
#         """
#         if (self.model.organizedByDate):
#             self.yearInput.ChangeValue(unicode(self.year))
#             self.monthInput.ChangeValue(unicode(self.month))
#             self.dayInput.ChangeValue(unicode(self.day))
#         else:
#             self.identifierString.SetLabel(self.name)
#             self.sceneInput.ChangeValue(unicode(self.scene))
#         # number applies to both organizations
#         self.numberInput.ChangeValue(unicode(self.number))
#         # elements apply to both organizations
#         self.setElementField()
#         # entry size
#         if (self.entry == None):
#             self.sizeString.SetLabel('')
#         else:
#             self.sizeString.SetLabel(self.entry.getSizeString())
# 
# 
#     def readInputFields(self):
#         """Read values from input fields into internal state. 
#         
#         This is used to combine a change from another function with changes in the input fields.
#         """
#         if (self.model.organizedByDate):
#             try:
#                 self.year = int(self.yearInput.GetValue())
#             except: 
#                 self.year = None
#             try:
#                 self.month = int(self.monthInput.GetValue())
#             except:
#                 self.month = None
#             try:
#                 self.day = int(self.dayInput.GetValue())
#             except: 
#                 self.day = None
#         else:
#             self.identifierString.SetLabel(self.name)
#             try:
#                 self.scene = int(self.sceneInput.GetValue())
#             except:
#                 self.scene = None
#         # number applies to both organizations
#         try:
#             self.number = int(self.numberInput.GetValue())
#         except: 
#             self.number = None
#         # elements apply to both organizations
#         self.knownElements = set()
#         self.unknownElements = set()
#         for element in self.model.getClassHandler().stringToElements(self.elementInput.GetValue()):
#             if (self.model.getClassHandler().isLegalElement(element)):
#                 self.knownElements.add(element)
#             else:
#                 self.unknownElements.add(element)
#     
#     

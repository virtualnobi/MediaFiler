#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""

# Imports
## standard
import logging
import os
import gettext
## contributed
import wx
## nobi
from nobi.ObserverPattern import Observer
## project
import UI
from UI import GUIId



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['de'])
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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
def N_(message): return message



class MediaNamePane(wx.Panel, Observer):
    """Panel displaying the file name components of the currently selected Entry. 
    
    Asks the model's organizationStrategy to add the fields relevant to the organization. 
    
    Observes the MediaCollection model for changes of selection, 
    and the Entry for changes of name.
    """
# Constants
    RenameImage = wx.NewIdRef()  # identifier of "Rename" button  TODO: move to GUIID
    ReuseLastElements = wx.NewIdRef()  # identifer of "Reuse Last" button  TODO: move to GUIID



# Class Methods    
# Lifecycle
    def __init__(self, parent, style=0):
        """Create a new pane to show and enter media names.
        
        wx.Window parent is the parent window to display the new pane
        """
        # style = (style | wx.FULL_REPAINT_ON_RESIZE)
        # inheritance
        wx.Panel.__init__(self, parent, style)
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
        self.GetSizer().Add(self.elementInput, proportion=1, flag=(  # wx.EXPAND |  EXPAND is forbidden with vertical alignment now...
                                                                   wx.ALIGN_CENTER_VERTICAL))
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
        if (entry != self.model.root):
            self.entry.organizer.setValuesInNamePane(self)
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
        self.renameEntry()


    def onRename(self, event):  # @UnusedVariable
        """User wants to rename the entry to values on UI. 
        
        Save the classification for later re-use.
        """
        self.renameEntry()



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
            self.setElementField()
            self.rememberElements()


# Other API Functions
    def Validate(self):
        """Recursively validate self.
        """
        if True:  # (super(MediaNamePane, self).Validate()):
            for widget in self.GetChildren():
                if ((widget.GetValidator()) 
                    and (not widget.GetValidator().Validate())): # (not widget.Validate()):
                    return(False)
            return(True)
        else:
            return(False)



# Internal
    def setElementField(self):
        """Set value of tag input field from selected entry.
        """
        knownTags = self.entry.getKnownTags(filtering=True)
        unknownTags= self.entry.getUnknownTags(filtering=True)
        elementString = self.model.getClassHandler().elementsToString(knownTags.union(unknownTags))
        self.elementInput.ChangeValue(elementString)

        
    def rememberElements(self):
        """Store tags from selected entry, for re-use. 
        """
        self.lastKnownElements = self.entry.getKnownTags()
        self.lastUnknownElements = self.entry.getUnknownTags()
        logging.debug('MediaNamePane.rememberElements(): Saved "%s" and "%s"' % (self.lastKnownElements, self.lastUnknownElements))


    def renameEntry(self, removeUnknownTags=False):
        """Rename the entry to the identifier and tags given in the input fields.

        If removeUnknownTags=False, the tags given in the tags input field are used. 
        If removeUnknownTags=True, illegal tags are removed, and the tags input field is ignored.

        Boolean removeUnknownTags indicates whether unknown tags shall be cleared from entry
        """
        if (self.Validate()):
            pathInfo = self.entry.getOrganizer().getPathInfo()
            pathInfo.update(self.entry.getOrganizer().getValuesFromNamePane(self))
            if (removeUnknownTags == False):
                tagString = self.elementInput.GetValue()
                tagSet = self.model.getClassHandler().stringToElements(tagString)
                pathInfo['elements'] = tagSet
            pathInfo['removeIllegalElements'] = removeUnknownTags
            try:
                with wx.GetApp() as processIndicator:
                    resultingSelection = self.entry.renameTo(processIndicator=processIndicator, **pathInfo)
            except WindowsError as e:
                dlg = wx.MessageDialog(self,
                                       ('Cannot rename media!\n%s' % e),
                                       'Error',
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                self.model.setSelectedEntry(resultingSelection) 
                self.rememberElements()



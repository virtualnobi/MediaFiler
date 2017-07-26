'''MediaFiler module

MediaNamePane is a subclass of wx.Panel displaying the file name components of the currently selected Entry.

The name pane keeps internal state (all name components) to be able to import changes to the entry 
selectively, e.g., import classification changes, but keep the current state of identifiers (scene, date). 

It observes the ImageTree for selection changes, and the selected Entry for name changes.
'''


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
# Constants
    ImageSizeFormat = '%dx%d'  # format string to display image size
    GroupSizeFormat = '%d images'  # format string to display group size
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
        self.components = {}
        self.classesToRemove = set()  # classes to clear; for removing classes from Groups
        self.lastElements = set()  # to assign the elements used last time again
        # add layout and fields
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))



# Setters
    def setModel (self, model):
        """Set the MODEL, to allow the correct configuration of identification fields.
        """
        #print('MediaNamePane.setModel()')
        # keep model reference
        if (self.model):
            self.model.removeObserver(self)
        self.model = model
        self.model.addObserverForAspect(self, 'selection')
        # remove sizer items
        while (len(self.GetSizer().GetChildren()) > 0):
            self.GetSizer().Remove(0)
        # padding item
        self.GetSizer().Add(wx.StaticText(self, -1, '  '))
        # depending on model organization, change fields for identification
        if (self.model.organizedByDate):
            # year
            self.yearInput = wx.TextCtrl (self, size=wx.Size(80,-1), style=wx.TE_PROCESS_ENTER)
            self.yearInput.Enable(True)
            self.yearInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.yearInput, flag=(wx.ALIGN_CENTER_VERTICAL))
            # padding item
            self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
            # month
            self.monthInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
            self.monthInput.Enable(True)
            self.monthInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.monthInput, flag=(wx.ALIGN_CENTER_VERTICAL))
            # padding item
            self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
            # day
            self.dayInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
            self.dayInput.Enable(True)
            self.dayInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.dayInput, flag=(wx.ALIGN_CENTER_VERTICAL))
            # padding item
            self.GetSizer().Add(wx.StaticText(self, -1, '/'), flag=(wx.ALIGN_CENTER_VERTICAL))
            # number
            self.numberInput = wx.TextCtrl (self, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
            self.numberInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        else:  # organized by name
            # name
            self.identifierString = wx.StaticText(self, -1, 'none')
            self.GetSizer().Add(self.identifierString, flag = (wx.ALIGN_CENTER_VERTICAL))
            # padding item
            self.GetSizer().Add(wx.StaticText(self, -1, '/'), flag=(wx.ALIGN_CENTER_VERTICAL))
            # scene 
            self.sceneInput = wx.TextCtrl (self, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
            self.sceneInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.sceneInput, flag=(wx.ALIGN_CENTER_VERTICAL))
            # padding item
            self.GetSizer().Add(wx.StaticText(self, -1, '-'), flag=(wx.ALIGN_CENTER_VERTICAL))
            # number
            self.numberInput = wx.TextCtrl (self, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
            self.numberInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
            self.GetSizer().Add(self.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # elements
        self.elementInput = wx.TextCtrl (self, style=wx.TE_PROCESS_ENTER)
        self.elementInput.Enable(True)
        self.elementInput.Bind(wx.EVT_TEXT_ENTER, self.onRename)
        self.GetSizer().Add(self.elementInput, proportion=1, flag=(wx.EXPAND | wx.ALIGN_CENTER_VERTICAL))
        self.classesToRemove = set()
        self.lastElements = set()
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
        self.GetSizer().Add(wx.StaticText(self, -1, '  '))  # padding
        self.sizeString = wx.StaticText(self, -1, '')
        self.GetSizer().Add(self.sizeString, flag=(wx.ALIGN_CENTER_VERTICAL))
        self.GetSizer().Add(wx.StaticText(self, -1, '  '))  # padding
        self.setEntry(self.model.getSelectedEntry())
        # relayout all of them
        self.GetSizer().Layout()


    def setEntry(self, entry):
        """Show the name elements of the selected entry.
        
        Model.Entry entry
        """
        logging.debug('MediaNamePane.setEntry(%s)' % entry.getPath())
        # establish observer pattern
        self.clear()
        self.entry = entry
        self.entry.addObserverForAspect(self, 'name')
        # initialize 
        self.classesToRemove = set()  # classes to remove; for Groups
        # fill components depending on organization of model
        if (entry <> self.model.root):
            self.entry.organizer.fillNamePane(self)
            self.knownElements = entry.getKnownElements()
            self.unknownElements = entry.getUnknownElements()
        # display components
        self.setInputFields()
        # layout again
        self.GetSizer().Layout()


# Getters
# Event Handlers
    def onLegalize(self, event):  # @UnusedVariable
        """User wants to remove all illegal elements from image name. 
        """
        if (self.entry.isGroup()):  # TODO: Let the Group handle this
            if (self.model.organizedByDate):
                self.readInputFields()  # ensure all other changes to input fields are kept
                self.unknownElements = set()  # remove unknown elements 
                self.renameEntry(True)
            else:  # organized by name 
                for subentry in self.entry.getSubEntries():
                    finalElements = subentry.getKnownElements()
                    print('Changing "%s" to elements %s' % (subentry.getPath(), finalElements))
                    subentry.renameTo(elements=finalElements)
            self.setEntry(self.entry)  # reflect changes in UI
        else:  # single file, either within a Group or outside of a Group
            self.readInputFields()  # ensure all other changes to input fields are kept
            self.unknownElements = set()  # remove unknown elements 
            self.renameEntry(True)


    def onReuseLastClasses (self, event):  # @UnusedVariable
        """User wants to assign the same classes as used in last class assignment.
        """
        self.readInputFields()  # ensure all other changes to input fields are kept
        self.knownElements = set()  # clear all elements
        self.unknownElements = set()
        for element in self.lastElements:  # set elements explicitly
            if (self.model.getClassHandler().isLegalElement(element)):
                self.knownElements.add(element)
            else:
                self.unknownElements.add(element)
        self.setInputFields()
        self.renameEntry(False)


    def onRename(self, event):  # @UnusedVariable
        """User wants to rename the entry. 
        
        Ensure the classification is saved for re-using it later.
        """
        self.readInputFields()
        self.lastElements = self.knownElements.union(self.unknownElements)
        self.renameEntry(False)



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
            self.readInputFields()
            if (self.model.organizedByDate):
                keepYear = self.year
                keepMonth = self.month
                keepDay = self.day
            else:
                keepName = self.name
                keepScene = self.scene
            keepNumber = self.number
            self.setEntry(self.entry)
            if (self.model.organizedByDate):
                self.year = keepYear
                self.month= keepMonth
                self.day = keepDay
            else:
                self.name = keepName
                self.scene = keepScene
            self.number = keepNumber
            self.setInputFields()
            self.lastElements = self.entry.getElements()
            print('MediaNamePane remembers elements %s' % self.lastElements)


# Other API Functions
# Internal
    def clear(self):
        """Clear all fields, since no Entry is selected
        """
        # clean up OberverPattern
        if (self.entry):  
            self.entry.removeObserver(self)  # unregister from previous observable
        self.entry = None
        # clear internal components
        if (self.model.organizedByDate):
            self.year = ''
            self.month = ''
            self.day = ''
            self.number = ''
        else:
            self.name = ''
            self.scene = ''
            self.number = ''
        self.knownElements = set()
        self.unknownElements = set()
        # display component values
        self.setInputFields()


    def setInputFields(self):
        """Set input fields from internal state.
        """
        if (self.model.organizedByDate):
            self.yearInput.ChangeValue(self.year)
            self.monthInput.ChangeValue(self.month)
            self.dayInput.ChangeValue(self.day)
        else:
            self.identifierString.SetLabel(self.name)
            self.sceneInput.ChangeValue(self.scene)
        # number applies to both organizations
        self.numberInput.ChangeValue(self.number)
        # elements apply to both organizations
        elementString = self.model.getClassHandler().elementsToString(self.knownElements.union(self.unknownElements))
        self.elementInput.ChangeValue(elementString)
        # entry size
        if (self.entry == None):
            self.sizeString.SetLabel('')
        else:
            self.sizeString.SetLabel(self.entry.getSizeString())


    def readInputFields(self):
        """Read values from input fields into internal state. 
        
        This is used to combine a change from another function with changes in the input fields.
        """
        if (self.model.organizedByDate):
            self.year = self.yearInput.GetValue()
            self.month = self.monthInput.GetValue()
            self.day = self.dayInput.GetValue()
        else:
            self.identifierString.SetLabel(self.name)
            self.scene = self.sceneInput.GetValue()
        # number applies to both organizations
        self.number = self.numberInput.GetValue()
        # elements apply to both organizations
        self.knownElements = set()
        self.unknownElements = set()
        for element in self.model.getClassHandler().stringToElements(self.elementInput.GetValue()):
            if (self.model.getClassHandler().isLegalElement(element)):
                self.knownElements.add(element)
            else:
                self.unknownElements.add(element)
    
    
    def renameEntry(self, removeUnkownTags=False):
        """Rename the entry, using the values from the internal state.
        
        Boolean removeUnknownTags indicates whether unknown tags shall be cleared from entry
        """
        pathInfo = self.entry.organizer.retrieveNamePane(self)
        pathInfo['elements'] = (self.knownElements.union(self.unknownElements))
        pathInfo['removeIllegalElements'] = removeUnkownTags
        success = self.entry.renameTo(pathInfo)
#         if (self.model.organizedByDate):  # TODO: move to self.entry.organizer()
#             result = self.entry.renameTo(year=self.year, 
#                                          month=self.month, 
#                                          day=self.day,
#                                          number=self.number,
#                                          elements=(self.knownElements.union(self.unknownElements)),
#                                          removeIllegalElements=removeUnkownTags)            
#         else:  # organized by name
#             result = self.entry.renameTo(name=self.name,
#                                          scene=self.scene, 
#                                          number=self.number,
#                                          elements=(self.knownElements.union(self.unknownElements)),
#                                          removeIllegalElements=removeUnkownTags)
        if (success):
            self.model.setSelectedEntry(self.entry)  # when switching groups, old parent group will change selection to itself 
        else:
            dlg = wx.MessageDialog(self, 
                                   'Cannot rename media!',
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()



'''
(c) by nobisoft 2015-
'''


# Imports
## standard
import gettext
import os.path
## contributed
import wx.lib.scrolledpanel
#import wx.lib.rcsizer
## nobi
from ObserverPattern import Observer
## project
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.MediaClassHandler import MediaClassHandler



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['de'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
    print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message



class MediaFilterPane (wx.lib.scrolledpanel.ScrolledPanel, Observer):
    """
    """



# Constants
    # rows in filter pane grid
    RowClear = 0  # row of "Clear" and "Apply" buttons
    RowSize = 1  # row of size sliders
    RowSingle = 2  # row of single/group condition
    RowUnknown = 3  # row of unknown elements (regular elements follow)
    # 
    SingleConditionIndex = 'single'  # string to access single/group condition
    SingleValueString = 'single'
    GroupValueString = 'group'
    # unknown elements
    UnknownElementsIndex = N_('unknown')  # string to access unknown filter in dictionary
    # special element to match any element of a class
    FilterElementValuesAnyIndex = 0  # index of any in value choice list
    FilterElementValuesAnyString = _('any')  # filter value to allow any value
    # filtering modes
    FilterModeNameIgnore = _('ignore')
    FilterModeIndexIgnore = 0
    FilterModeNameRequire = _('require')
    FilterModeIndexRequire = 1
    FilterModeNameExclude = _('exclude')
    FilterModeIndexExclude = 2
    FilterModeNames = [FilterModeNameIgnore, FilterModeNameRequire, FilterModeNameExclude]
    # Labels
    FileSizeLabel = _('Size:')



# Class Variables
# Class Methods
# Lifecycle
    def __init__ (self, parent, style=0):
        # initialize superclass
        wx.lib.scrolledpanel.ScrolledPanel.__init__ (self, parent, id=-1, size=wx.Size (450, 0), style=(style | wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        self.SetAutoLayout (1)
        self.SetupScrolling ()
        # init variables
        self.imageModel = None  # ImageFilerModel, to derive filter from
        self.filterModel = None  # MediaFilter, to manage filter conditions
        self.filterModes = {}  # Dictionary mapping class name to filter mode wx.Choice
        self.filterValues = {}  # Dictionary mapping class name to filter value wx.Choice
       


# Setters
    def releaseModel(self):
        """Release all data related to the model, including widgets
        """
        if (self.imageModel):
            self.imageModel.removeObserver(self)
#             self.imageModel = None
#             if (self.filterModel):
#                 self.filterModel.removeObserver(self)
#                 self.filterModel = None
#             self.clearButton = None
#             self.applyButton = None
# #             for idx in range(len(self.GetSizer().GetChildren())-1, -1, -1):
# #                 self.GetSizer().Detach(idx)
#             for w in self.GetSizer().GetChildren():
#                 w.Detach(self.GetSizer())
#             #self.GetSizer().DeleteWindows()
#             self.SetSizer(None)


    def setModel(self, anImageFilerModel):
        """Make anImageFilerModel the model of self, and create widgets on self accordingly.
        """
        # store MediaFiler model
        self.releaseModel()
        if (self.imageModel <> None):  # release previous model
            self.imageModel.removeObserver(self)
        self.imageModel = anImageFilerModel
        # store filter model
        if (self.filterModel <> None):  # release previous filter model
            self.filterModel.removeObserver(self)
        self.filterModel = self.imageModel.getFilter()
        self.filterModel.addObserverForAspect(self, 'changed')
        # create empty lists of wx.Choice controls for each class, for modes and values
        self.filterModes = {}
        self.filterValues = {}
        # create one row per class with class name, value, and mode
        classes = self.imageModel.getClassHandler().getClasses()
        gridSizer = wx.GridBagSizer(3, 3)
        row = 0
        # add clear and apply buttons
        buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.clearButton = wx.Button(self, id=GUIId.ClearFilter, label=GUIId.FunctionNames[GUIId.ClearFilter])
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear, id=GUIId.ClearFilter)
        buttonBox.Add(self.clearButton, 0, wx.EXPAND)
        self.applyButton = wx.Button(self, id=GUIId.ApplyFilter, label=GUIId.FunctionNames[GUIId.ApplyFilter])
        self.applyButton.Bind(wx.EVT_BUTTON, self.onApply, id=GUIId.ApplyFilter)
        buttonBox.Add(self.applyButton, 0, wx.EXPAND)
        gridSizer.Add(buttonBox, (row, 0), (1, 3))
        gridSizer.Add(wx.BoxSizer(), (row + 1, 0), (1, 1))
        row = (row + 2)
        # add "unknown elements" condition
        self.addUnknownFilter(gridSizer, row)
        gridSizer.Add(wx.BoxSizer(), (row + 1, 0), (1, 1))
        row = (row + 2)
        # add classes with all their elements
        for aClass in classes:
            # create choice of class values
            choices = []
            choices.extend(self.imageModel.getClassHandler().getElementsOfClass(aClass))
            choices.sort()
            if (len(choices) > 1):  # more than one element for this class, add an all-class filter
                choices.insert(self.FilterElementValuesAnyIndex, self.FilterElementValuesAnyString)
            valueChoice = wx.Choice(self, -1, choices=choices)
            valueChoice.SetSelection(self.FilterElementValuesAnyIndex)
            self.Bind(wx.EVT_CHOICE, self.onValueChanged, valueChoice)
            self.filterValues[aClass[MediaClassHandler.KeyName]] = valueChoice
            self.addTextFilter(gridSizer, row, aClass[MediaClassHandler.KeyName], valueChoice)
            # advance row count
            row = (row + 1)
        gridSizer.Add(wx.BoxSizer(), (row, 0), (1, 1))
        row = (row + 1)
        # add minimum/maximum size filter
        self.addSizeFilter(gridSizer, row)
        gridSizer.Add(wx.BoxSizer(), (row + 1, 0), (1, 1))
        row = (row + 2)
        # add date range
        if (self.imageModel.organizedByDate):
            pass  # TODO:
        # add single/group condition
        if (not self.imageModel.organizedByDate):
            singleText = wx.StaticText(self, -1, self.SingleConditionIndex)
            self.addTextFilter(gridSizer, row, self.SingleConditionIndex, singleText)        
            row = (row + 1)
        # set overall sizer
        self.SetSizer(gridSizer) 
        gridSizer.Layout()
        # import filter conditions
        self.importAndDisplayFilter()


#     def setFilter(self, required, prohibited, unknown, single):
#         '''Set the current filter, and update self's widgets accordingly.
#         
#         required - a Sequence of Strings containing required class elements
#         prohibited - a Sequence of Strings containing prohibited class elements
#         unknown - a Boolean indicating whether unknown elements are required
#         Boolean single whether to filter Singles or Groups (None if no filtering)
#         
#         Returns a Boolean indicating whether the new filter differs from the old.
#         '''
#         print('MediaFilterPane.setFilter() deprecated')
#         changed = ((self.requiredElements <> required)
#                    or (self.prohibitedElements <> prohibited)
#                    or (self.unknownElementRequired <> unknown)
#                    or (self.single <> single))
#         if (changed):  # filter criteria must change, update widgets
#             self.filterModel.setconditions(required=required,  
#                                            prohibited=prohibited, 
#                                            unknownRequired=unknown,
#                                            single=single)
#             self.requiredElements = required
#             self.prohibitedElements = prohibited
#             self.unknownElementRequired = unknown
#             self.singleCondition = single
#         return(changed)



# Getters    
#     def getFilter(self): 
#         '''Get the current filter. 
#         
#         Returns (required, prohibited, unknown, single) as defined in setFilter.
#         '''
#         print('MediaFilterPane.getFilter() deprecated')
#         return (self.requiredElements, self.prohibitedElements, self.unknownElementRequired, self.singleCondition)



# Event Handlers
    def onClear(self, event):  # @UnusedVariable
        """User wants to clear the filter.
        """
        wx.BeginBusyCursor()
        self.filterModel.clear()
        wx.EndBusyCursor()


    def onApply(self, event):  # @UnusedVariable
        """
        """
        wx.BeginBusyCursor()
        self.filterModel.setConditions(active=True)
        wx.EndBusyCursor()


    def onModeChanged(self, event):  # @UnusedVariable
        """User changed a mode in the filter. Update internal state. 
        """
        wx.BeginBusyCursor()
        # TODO: Check whether class definition requires (de)activation of other choices
        # clear existing filters
        self.requiredElements = set()
        self.prohibitedElements = set()
        # filter for single/group
        if (not self.imageModel.organizedByDate):
            modeName = self.filterModes[self.SingleConditionIndex].GetStringSelection()
            if (modeName == self.FilterModeNameRequire):
                self.singleCondition = True
            elif (modeName == self.FilterModeNameExclude):
                self.singleCondition = False
            else:  # must be ignore
                self.singleCondition = None
        # set up value filter for unknown values
        modeName = self.filterModes[self.UnknownElementsIndex].GetStringSelection()
        valueName = self.filterValues[self.UnknownElementsIndex].GetValue()
        if (modeName == self.FilterModeNameRequire):
            if (valueName == ''):
                self.unknownElementRequired = True
            else:
                self.requiredElements.add(valueName)
        elif (modeName == self.FilterModeNameExclude):
            if (valueName == ''):
                self.unknownElementRequired = False
            else:
                self.prohibitedElements.add(valueName)
        else:  # must be ignore
            self.unknownElementRequired = False
        # for all classes, set up value filters
        for className in self.imageModel.getClassHandler().getClassNames():
            # TODO: make checkbox conditions work
            modeName = self.filterModes[className].GetStringSelection()
            valueName = self.filterValues[className].GetStringSelection()
            if (modeName == self.FilterModeNameRequire):
                if (valueName == self.FilterElementValuesAnyString):
                    self.requiredElements.add(className)
                else:
                    self.requiredElements.add(valueName)
            elif (modeName == self.FilterModeNameExclude):
                if (valueName == self.FilterElementValuesAnyString):
                    self.prohibitedElements.add(className)
                else:
                    self.prohibitedElements.add(valueName)
            else:  # must be 'ignore'
                pass
        # update filter model
        self.filterModel.setConditions(required=self.requiredElements, 
                                       prohibited=self.prohibitedElements, 
                                       unknownRequired=self.unknownElementRequired,
                                       single=self.singleCondition)
        wx.EndBusyCursor()


    def onValueChanged(self, event):
        """User change an element value in filter. Update internal state.
        
        In addition to the regular update done in onModeChanged(), 
        the mode corresponding to the value is set to Require if it was Ignore.
        """
        for key in self.filterValues:
            if (self.filterValues[key] == event.GetEventObject()):
                if (self.filterModes[key].GetStringSelection() == self.FilterModeNameIgnore):
                    self.filterModes[key].SetStringSelection(self.FilterModeNameRequire)
        return(self.onModeChanged(event))


    def onSliderChanged(self, event):
        """User changed the size slider.
        """
        wx.BeginBusyCursor()
        print('Slider changed to %d' % event.EventObject.GetValue())
        if (event.EventObject == self.minimumSlider):
            self.maximumSliderMinimum = event.EventObject.GetValue()  # minimum slider position is new minimum for maximum slider
            self.maximumSlider.SetMin(self.maximumSliderMinimum)
            self.filterModel.setConditions(minimum=self.maximumSliderMinimum)
        else:
            self.minimumSliderMaximum = event.EventObject.GetValue()  # maximum slider position is new maximum for minimum slider
            self.minimumSlider.SetMax(self.minimumSliderMaximum)
            self.filterModel.setConditions(maximum=self.minimumSliderMaximum)
        wx.EndBusyCursor()



# Inheritance - Observer
    def updateAspect(self, observable, aspect):
        """ ASPECT of OBSERVABLE has changed. 
        """
        if (aspect == 'changed'):
            self.importAndDisplayFilter()



# Internal
    def addTextFilter(self, sizer, row, filterKey, control):
        '''Add a filter criterion to self, and insert the corresponding controls into self's Sizer.
        
        wx.GridBagSizer sizer  for layouting   
        Number row             the row to use in sizer
        String filterkey       "unknown" or the class name
        wx.?? control          the control to enter the filter value (TextCtrl or Choice)
        Returns                -
        '''
        # filter label
        if (filterKey == self.UnknownElementsIndex):
            label = _(filterKey)
        else:
            label = filterKey
        sizer.Add(wx.StaticText(self, -1, (label + ':')), (row, 0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # add control to specify value
        sizer.Add(control, (row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        # create choice of mode, linking to the value choice 
        modeChoice = wx.Choice(self, -1, choices=self.FilterModeNames)
        modeChoice.SetSelection(self.FilterModeIndexIgnore)
        self.filterModes[filterKey] = modeChoice
        sizer.Add(modeChoice, (row, 2), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHOICE, self.onModeChanged, modeChoice)

    
    def addUnknownFilter(self, sizer, row):
        """Add a textfield to require/prohibit unknown elements. 
        """
        unknownElements = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)  # text to enter unknown elements
        unknownElements.Enable(True)
        self.filterValues[self.UnknownElementsIndex] = unknownElements 
        self.Bind(wx.EVT_TEXT_ENTER, self.onValueChanged, unknownElements)
        self.addTextFilter(sizer, row, self.UnknownElementsIndex, unknownElements)


    def addSizeFilter(self, sizer, row):
        """
        """
        # label
        sizer.Add(wx.StaticText(self, -1, self.FileSizeLabel), (row, 0), (1,1), flag=wx.ALIGN_RIGHT)
        # minimum
        if (0 < self.filterModel.maximumSize):  # == 0):  # maximum size requirement
            self.minimumSliderMaximum = self.filterModel.maximumSize  # minimum can only move to max requirement 
        else:  # no max requirement
            self.minimumSliderMaximum = self.imageModel.getMaximumSize()
        self.minimumSlider = wx.Slider(self, -1, 
                                       self.filterModel.minimumSize,  # initial slider value 
                                       self.imageModel.getMinimumSize(),  # slider minimum
                                       self.minimumSliderMaximum,  # slider maximum
                                       (30, 60),  # ?
                                       (100, -1),  # size
                                       (wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_BOTTOM))  # styles, wx.SL_SELRANGE only on Windows95
        self.minimumSlider.SetTickFreq(500, 1)
        self.minimumSlider.Bind(wx.EVT_SCROLL_CHANGED, self.onSliderChanged)
        sizer.Add(self.minimumSlider, (row, 1), (1, 1), flag=wx.ALIGN_LEFT)
        # add size sliders - maximum
        if (0 < self.filterModel.minimumSize):  # minimum size requirement
            self.maximumSliderMinimum = self.filterModel.minimumSize  # maximum can only move to min requirement
        else:  # no min requirement
            self.maximumSliderMinimum = self.imageModel.getMinimumSize()
        self.maximumSlider = wx.Slider(self, -1, 
                                       self.filterModel.maximumSize,  # initial slider value 
                                       self.maximumSliderMinimum,  # slider minimum
                                       self.imageModel.getMaximumSize(),  # slider maximum
                                       (30, 60),  # ?
                                       (100, -1),  # size
                                       (wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_BOTTOM))  # styles, wx.SL_SELRANGE only on Windows95
        self.maximumSlider.SetTickFreq(500, 1)
        self.maximumSlider.Bind(wx.EVT_SCROLL_CHANGED, self.onSliderChanged)
        sizer.Add(self.maximumSlider, (row, 2), (1, 1), flag=wx.ALIGN_RIGHT)


    def importAndDisplayFilter(self):
        """Redisplay  filter criteria. 
        """
        (active,
         self.requiredElements,
         self.prohibitedElements,
         self.unknownElementRequired,
         self.minimumFileSize,
         self.maximumSize,
         self.singleCondition,
         self.fromDate,
         self.toDate) = self.filterModel.getFilterConditions()
        # single/group condition
        if (not self.imageModel.organizedByDate):
            if (self.singleCondition == None):
                self.filterModes[self.SingleConditionIndex].SetSelection(self.FilterModeIndexIgnore)
            elif (self.singleCondition == True):
                self.filterModes[self.SingleConditionIndex].SetSelection(self.FilterModeIndexRequire)
            elif (self.singleCondition == False):
                self.filterModes[self.SingleConditionIndex].SetSelection(self.FilterModeIndexExclude)
        # unknown elements
        if (self.filterModel.unknownElementRequired):
            self.filterModes[self.UnknownElementsIndex].SetSelection(self.FilterModeIndexRequire)
        else:
            self.filterModes[self.UnknownElementsIndex].SetSelection(self.FilterModeIndexIgnore)
            for tag in self.requiredElements: 
                if (not self.imageModel.getClassHandler().isLegalElement(tag)):
                    self.filterValues[self.UnknownElementsIndex].SetValue(tag)
                    self.filterModes[self.UnknownElementsIndex].SetSelection(self.FilterModeIndexRequire)
            for tag in self.prohibitedElements:
                if (not self.imageModel.getClassHandler().isLegalElement(tag)):
                    self.filterValues[self.UnknownElementsIndex].SetValue(tag)
                    self.filterModes[self.UnknownElementsIndex].SetSelection(self.FilterModeIndexExclude)    
        # class elements
        for className in self.imageModel.getClassHandler().getClassNames():
            # reset to no filtering
            self.filterModes[className].SetSelection(self.FilterModeIndexIgnore)
            self.filterValues[className].SetSelection(self.FilterModeIndexIgnore)
            if (className in self.filterModel.requiredElements):
                self.filterModes[className].SetSelection(self.FilterModeIndexRequire)
                self.filterValues[className].SetStringSelection(self.FilterElementValuesAnyString)
            elif (className in self.filterModel.prohibitedElements):
                self.filterModes[className].SetSelection(self.FilterModeIndexExclude)
                self.filterValues[className].SetStringSelection(self.FilterElementValuesAnyString)
            else:
                for element in self.imageModel.getClassHandler().getElementsOfClassByName(className):
                    if (element in self.filterModel.requiredElements):
                        #print('Showing required "%s" in "%s"' % (element, className))
                        self.filterModes[className].SetSelection(self.FilterModeIndexRequire)
                        self.filterValues[className].SetStringSelection(element)
                    elif (element in self.filterModel.prohibitedElements):
                        #print('Showing prohibited "%s" in "%s"' % (element, className))
                        self.filterModes[className].SetSelection(self.FilterModeIndexExclude)
                        self.filterValues[className].SetStringSelection(element)
        # button activation
        self.clearButton.Enable(enable=(not self.filterModel.isEmpty()))
        self.applyButton.Enable(enable=(not active))



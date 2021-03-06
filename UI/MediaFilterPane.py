'''
(c) by nobisoft 2015-
'''


# Imports
## standard
import gettext
import os.path
import logging
import re
## contributed
import wx.lib.scrolledpanel
## nobi
from nobi.ObserverPattern import Observer
## project
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.MediaClassHandler import MediaClassHandler
from Model.Single import Single
from Model.MediaFilter import MediaFilter



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



# Package Variables
Logger = logging.getLogger(__name__)



class FilterCondition(Observer):
    """Displays a filter condition. 
    """
    def __init__(self, parent, label):  # @UnusedVariable
        """Create a filter condition.
        
        Create input controls as needed to define the filter condition. These controls must
        be returned by getConditionControls() to be added to the MediaFilterPane. Register
        onChange() as handler for these controls, and update the filterModel accordingly.
        When the filterModel changes, updateAspect() will be called and needs to change the
        input controls. 
        
        The instance variables collectionModel and filterModel will be set after __init__ when 
        self is added to the MediaFilterPane. 
        
        wx.Window parent specifies the parent window for filtering controls
        String label specifies the field label
        """
        self.label = label
        self.collectionModel = None
        self.filterModel = None


    def getLabel(self):
        """Return the string to be used as filter label
        """
        return(self.label)


    def getConditionControls(self):
        """Return an array containing 1 or 2 controls to input self's condition.
        
        These controls will be added to the MediaFilterPane during initialization. 
        """
        raise NotImplementedError


    def getFilterModel(self):
        return(self.filterModel)


    def setCollectionModel(self, aMediaCollection):
        self.collectionModel = aMediaCollection


    def setFilterModel(self, aMediaFilter):
        try:
            self.filterModel.removeObserver(self)
        except: 
            pass
        self.filterModel = aMediaFilter
        self.filterModel.addObserverForAspect(self, 'changed')


    def onChange(self, event):
        raise NotImplementedError


    def updateAspect(self, aspect, observable):
        raise NotImplementedError



class FilterConditionWithMode(FilterCondition):
    """Represents a filter condition with a mode choice control (ignore, required, prohibited).
    
    self.modeChoice contains a wx.Choice with these three options.
    """
    FilterModeNameIgnore = _('ignore')
    FilterModeNameRequire = _('require')
    FilterModeNameExclude = _('exclude')
    FilterModeNames = [FilterModeNameIgnore, FilterModeNameRequire, FilterModeNameExclude]
    FilterModeIndexIgnore = FilterModeNames.index(FilterModeNameIgnore)  # 0
    FilterModeIndexRequire = FilterModeNames.index(FilterModeNameRequire)  # 1
    FilterModeIndexExclude = FilterModeNames.index(FilterModeNameExclude)  # 2
    

    def __init__(self, parent, label):
        FilterCondition.__init__(self, parent, label)
        self.modeChoice = wx.Choice(parent, wx.ID_ANY, choices=FilterConditionWithMode.FilterModeNames)
        self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexIgnore)
        self.modeChoice.Bind(wx.EVT_CHOICE, self.onChange, self.modeChoice)



class BooleanFilter(FilterConditionWithMode):
    """Represents a filter for a boolean condition.
    """
    def __init__(self, parent, label, conditionKey):
        """Create a controls for a boolean condition.
        
        wx.Window  parent
        String     label is the condition label
        String     conditionKey is the internal key of the condition, see MediaFilter.getConditionKeys()
        """
        FilterConditionWithMode.__init__(self, parent, label)
        self.conditionKey = conditionKey


    def getConditionControls(self):
        return([self.modeChoice])


    def onChange(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        newMode = self.modeChoice.GetSelection()
        if (newMode == FilterConditionWithMode.FilterModeIndexRequire):
            newFilterValue = True
        elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
            newFilterValue = False
        else:
            newFilterValue = None
        Logger.debug('BooleanFilter.onChange(): Changing mode of "%s" to "%s"' % (self.conditionKey, newFilterValue))
        self.filterModel.setFilterValueFor(self.conditionKey, newFilterValue)
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('BooleanFilter.updateAspect(): Processing change of "%s" filter' % self.conditionKey)
            newFilterValue = self.filterModel.getFilterValueFor(self.conditionKey)
            if (newFilterValue == True):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexRequire)
            elif (newFilterValue == False):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexExclude)
            else:
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexIgnore)
            Logger.debug('BooleanFilter.updateAspect(): Setting "%s" to "%s"' % (self.conditionKey, newFilterValue))
        else:
            Logger.error('BooleanFilter.updateAspect(): Unknown aspect "%s" of object "%s" on "%s"' % (aspect, observable, self.conditionKey))


    
class TagFilter(FilterConditionWithMode):
    """Represents a tag filter.
    """
    def __init__(self, parent, tagClass, tagList):
        FilterConditionWithMode.__init__(self, parent, tagClass)
        self.valueChoice = wx.Choice(parent, -1, choices=tagList)
        self.valueChoice.SetSelection(self.FilterElementValuesAnyIndex)


    def getConditionControls(self):
        return([self.valueChoice, self.modeChoice])



class UnknownTagFilter(FilterConditionWithMode):
    """Represents a filter for unknown tags
    """
    def __init__(self, parent):
        FilterConditionWithMode.__init__(self, parent, _('Unknown Tag'))
        self.tagInput = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)
        self.tagInput.Enable(True)
        self.tagInput.Bind(wx.EVT_TEXT_ENTER, self.onChange, self.tagInput)


    def getConditionControls(self):
        return([self.tagInput, self.modeChoice])


    def onChange(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        source = event.GetEventObject()
        textValue = self.tagInput.GetValue()
        newMode = self.modeChoice.GetSelection()
        newTags = re.split('\W+', textValue)
        if ('' in newTags):
            newTags.remove('')
        if (source == self.tagInput):
            Logger.debug('UnknownTagFilter.onChange(): Processing change of tags to "%s"' % newTags)
            if (newMode == FilterConditionWithMode.FilterModeIndexIgnore):
                if (0 == len(newTags)): 
                    self.filterModel.setConditions(requiredUnknownTags=set(), 
                                                   prohibitedUnknownTags=set(), 
                                                   unknownRequired=None)
                else:  # newTags contains tags, turn on filtering
                    self.filterModel.setConditions(requiredUnknownTags=newTags,
                                                   prohibitedUnknownTags=set(),
                                                   unknownRequired=True)
            elif (newMode == FilterConditionWithMode.FilterModeIndexRequire):
                self.filterModel.setConditions(requiredUnknownTags=newTags,
                                               prohibitedUnknownTags=set(),
                                               unknownRequired=True)
            elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
                self.filterModel.setConditions(requiredUnknownTags=set(),
                                               prohibitedUnknownTags=newTags,
                                               unknownRequired=False)
        elif (source == self.modeChoice):
            Logger.debug('UnknownTagFilter.onChange(): Processing change of mode to "%s"' % newMode)
            if (newMode == FilterConditionWithMode.FilterModeIndexIgnore):
                self.filterModel.setConditions(unknownRequired=None)
            elif (newMode == FilterConditionWithMode.FilterModeIndexRequire):
                self.filterModel.setConditions(requiredUnknownTags=newTags,
                                               prohibitedUnknownTags=set(),
                                               unknownRequired=True)
            elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
                self.filterModel.setConditions(requiredUnknownTags=set(),
                                               prohibitedUnknownTags=newTags,
                                               unknownRequired=False)
        else:
            raise ValueError('UnknownTagFilter.onChange(): Unknown event source!')
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('UnknownTagfilter.updateAspect(): Processing change of filter')
            requiredUnknownTags = observable.getRequiredUnknownTags()
            prohibitedUnknownTags = observable.getProhibitedUnknownTags()
            unknownRequired = observable.getIsUnknownTagRequired()
            # TODO: unknownRequired must have highest prio, specification of tags has second priority
            if (unknownRequired == True):
                Logger.debug('UnknownTagfilter.updateAspect(): Setting to unknown required')
                self.tagInput.SetValue(' '.join(requiredUnknownTags))
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexRequire)
            elif (unknownRequired == False):
                Logger.debug('UnknownTagfilter.updateAspect(): Setting to unknown prohibited')
                self.tagInput.SetValue(' '.join(prohibitedUnknownTags))
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexExclude)
            else:
                Logger.debug('UnknownTagfilter.updateAspect(): Neither unknown tags, nor unknown required, setting to ignore')
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexIgnore)
                if (0 < len(requiredUnknownTags)):
                    Logger.debug('UnknownTagfilter.updateAspect(): Setting to require unknown tags')
                    self.tagInput.SetValue(' '.join(requiredUnknownTags))
                elif (0 < len(prohibitedUnknownTags)):
                    Logger.debug('UnknownTagfilter.updateAspect(): Setting to exclude unknown tags')
                    self.tagInput.SetValue(' '.join(prohibitedUnknownTags))
        else:
            Logger.error('UnknownTagFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))



class MediaTypeFilter(FilterCondition):
    """Represents a filter for the media type
    """
    def __init__(self, parent):
        FilterCondition.__init__(self, parent, _('Media Type'))
        self.mediaTypes = sorted(Single.__subclasses__(), key=lambda c:c.__name__)  # @UndefinedVariable
        mediaTypeNames = [cls.getMediaTypeName() for cls in self.mediaTypes]
        self.typeChoice = wx.CheckListBox(parent, -1, wx.DefaultPosition, wx.DefaultSize, mediaTypeNames)
        self.typeChoice.Bind(wx.EVT_CHECKLISTBOX, self.onChange, self.typeChoice)


    def getConditionControls(self):
        return([self.typeChoice])


    def onChange(self, event):
        wx.BeginBusyCursor()
        source = event.GetEventObject()
        changedIndex = event.GetSelection()
        changedMediaType = self.mediaTypes[changedIndex]
        (required, prohibited) = self.filterModel.getMediaTypes()  # @UnusedVariable
        if (source.IsChecked(changedIndex)):
            required.add(changedMediaType)
        else:
            if (changedMediaType in required):
                required.remove(changedMediaType)
            else:
                logging.error('MediaTypeFilter.onChange(): media type %s not in filter!' % changedMediaType.__name__)
        self.filterModel.setConditions(requiredMediaTypes=required)
        source.SetSelection(changedIndex)  # put focus on (un)checked type
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('MediaTypeFilter.updateAspect(): Processing change of filter')
            self.typeChoice.SetCheckedItems([]) 
            (required, prohibited) = self.filterModel.getMediaTypes()  # @UnusedVariable
            requiredTypeIndices = [self.mediaTypes.index(mediaType) for mediaType in required]
            self.typeChoice.SetCheckedItems(requiredTypeIndices)
            Logger.debug('MediaTypeFilter.updateAspect(): Set %d required types' % len(requiredTypeIndices))
        else:
            Logger.error('MediaTypeFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))



class MediaSizeFilter(FilterCondition):
    """Represents a filter for media size
    """
    def __init__(self, parent):
        FilterCondition.__init__(self, parent, _('Size (%)'))
        self.minimumPercent = 0
        self.maximumPercent = 100
        # minimum
        self.minimumSlider = wx.Slider(parent, -1, 
                                       self.minimumPercent,  # initial slider value 
                                       self.minimumPercent,  # slider minimum
                                       self.maximumPercent,  # slider maximum
                                       (30, 60),  # ?
                                       (100, -1),  # size
                                       (wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_BOTTOM))  # styles, wx.SL_SELRANGE only on Windows95
#         self.minimumSlider.SetTickFreq(10, 1)
        self.minimumSlider.SetTickFreq(10)  # wxPython 4
        self.minimumSlider.Bind(wx.EVT_SCROLL_CHANGED, self.onChange)
        # maximum
        self.maximumSlider = wx.Slider(parent, -1, 
                                       self.maximumPercent,  # initial slider value 
                                       self.minimumPercent,  # slider minimum
                                       self.maximumPercent,  # slider maximum
                                       (30, 60),  # ?
                                       (100, -1),  # size
                                       (wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_BOTTOM))  # styles, wx.SL_SELRANGE only on Windows95
#         self.maximumSlider.SetTickFreq(10, 1)
        self.maximumSlider.SetTickFreq(10)  # wxPython 4
        self.maximumSlider.Bind(wx.EVT_SCROLL_CHANGED, self.onChange)


    def getConditionControls(self):
        return([self.minimumSlider, self.maximumSlider])


    def onChange(self, event):
        wx.BeginBusyCursor()
        source = event.GetEventObject()
#        variation = (self.collectionModel.getMaximumResolution() - self.collectionModel.getMinimumResolution())
        Logger.debug('MediaSizeFilter.onChange(): Media resolution changed to %s' % source.GetValue())
        if (source == self.minimumSlider):
            self.minimumPercent = source.GetValue()
            self.maximumSlider.SetMin(source.GetValue())
#             minimumResolution = (self.collectionModel.getMinimumResolution() + (self.minimumPercent / 100.0 * variation))
#             Logger.debug('MediaSizeFilter.onChange(): Minimum resolution set to %s from %s%%' % (minimumResolution, self.minimumPercent))
#             self.filterModel.setConditions(minimum=minimumResolution)
            Logger.debug('MediaSizeFilter.onChange(): Minimum resolution set to %s%%' % self.minimumPercent)
            self.filterModel.setConditions(minimum=self.minimumPercent)
        else:
            self.maximumPercent = source.GetValue()
            self.minimumSlider.SetMax(self.maximumPercent)
#             maximumResolution = (self.collectionModel.getMinimumResolution() + (self.maximumPercent / 100.0 * variation))
#             Logger.debug('MediaSizeFilter.onChange(): Maximum resolution set to %s from %s%%' % (maximumResolution, self.maximumPercent))
#             self.filterModel.setConditions(maximum=maximumResolution)
            Logger.debug('MediaSizeFilter.onChange(): Maximum resolution set to %s%%' % self.maximumPercent)
            self.filterModel.setConditions(maximum=self.maximumPercent)
        # self.minimumSlider.GetParent().GetSizer().Layout()  # TODO: Does not relayout. How to do? 
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if ((aspect == 'changed')
            and (observable == self.filterModel)):
            if (self.filterModel.getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum) != None):
                self.minimumPercent = self.filterModel.getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum)
                self.minimumSlider.SetValue(self.minimumPercent)
                self.maximumSlider.SetMin(self.minimumPercent)
                Logger.debug('MediaSizeFilter.updateAspect(): Set minimum percent to %s' % self.minimumPercent)
            if (self.filterModel.getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum) != None):
                self.maximumPercent = self.filterModel.getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum)
                self.maximumSlider.SetValue(self.maximumPercent)
                self.minimumSlider.SetMax(self.maximumPercent)
                Logger.debug('MediaSizeFilter.updateAspect(): Set maximum percent to %s' % self.maximumPercent)
        else:
            Logger.error('MediaSizeFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))




class MediaFilterPane(wx.lib.scrolledpanel.ScrolledPanel, Observer):
    """A scrollable, observable Pane which visualizes the filter.
    """
# Constants
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



# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, style=0, size=wx.Size(450,0)):
        # inheritance
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, size=size, style=(style | wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        # internal state
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.clearModel()



# Setters
    def clearModel(self):
        """Release all data related to the model, including widgets
        """
        # clear dependencies
        try: 
            self.imageModel.removeObserver(self)
        except: 
            pass
        self.imageModel = None
        try:
            self.filterModel.removeObserver(self)
        except:
            pass
        self.filterModel = None
        # clear widgets
        self.DestroyChildren()
        self.gridSizer = wx.GridBagSizer(2, 3)
        self.usedGridRows = 0
        # clear internal state
        self.filterConditions = {}
        self.filterModes = {}  # Dictionary mapping class name to filter mode wx.Choice
        self.filterValues = {}  # Dictionary mapping class name to filter value wx.Choice


    def setModel(self, anImageFilerModel):
        """Make anImageFilerModel the model of self, and create widgets on self accordingly.
        """
        Logger.debug('MediaFilterPane.setModel(')
        self.clearModel()
        self.imageModel = anImageFilerModel
        self.filterModel = self.imageModel.getFilter()
        self.filterModel.addObserverForAspect(self, 'changed')
        classes = self.imageModel.getClassHandler().getClasses()
        # add button toolbar
        buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.activateButton = wx.ToggleButton(self, -1, 'Filter')
        self.activateButton.Bind(wx.EVT_TOGGLEBUTTON, self.onActivate)
        self.setActivateButtonText()
        buttonBox.Add(self.activateButton, 0, wx.EXPAND)
        self.clearButton = wx.Button(self, id=GUIId.ClearFilter, label=GUIId.FunctionNames[GUIId.ClearFilter])
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear, id=GUIId.ClearFilter)
        buttonBox.Add(self.clearButton, 0, wx.EXPAND)
        self.gridSizer.Add(buttonBox, (self.usedGridRows, 0), (1, 3))
        self.usedGridRows = (self.usedGridRows + 1)
        self.addSeparator()
        # filter area
        self.unknownFilterRow = self.addCondition(UnknownTagFilter(self))
        self.addSeparator()
        # create one row per class with class name, value, and mode
        for aClass in classes:
            Logger.debug('MediaFilterPane.setModel(): creating controls for class %s' % aClass[MediaClassHandler.KeyName])
            # create choice of class values
            choices = []
            choices.extend(self.imageModel.getClassHandler().getElementsOfClass(aClass))
            choices.sort()
            if (len(choices) > 1):  # more than one element for this class, add an all-class filter
                choices.insert(self.FilterElementValuesAnyIndex, self.FilterElementValuesAnyString)
            valueChoice = wx.Choice(self, -1, choices=choices)
            valueChoice.SetSelection(self.FilterElementValuesAnyIndex)
            self.Bind(wx.EVT_CHOICE, self.onValueChanged, valueChoice)
            self.addTextFilter(self.gridSizer, self.usedGridRows, aClass[MediaClassHandler.KeyName], aClass[MediaClassHandler.KeyName], valueChoice)
            # advance row count
            self.usedGridRows = (self.usedGridRows + 1)
        self.addSeparator()
        # add other filters
        self.sizeFilterRow = self.addCondition(MediaSizeFilter(self))
        self.mediaTypeFilterRow = self.addCondition(MediaTypeFilter(self))
        self.duplicateFilter = self.addCondition(BooleanFilter(self, _('Duplicates'), MediaFilter.ConditionKeyDuplicate))
        self.addSeparator()
        # add organization-specific filters
        self.imageModel.organizationStrategy.initFilterPane(self)
#         # add new-style conditions
#         addConditionButton = wx.Button(self, id=0, label=_('Add Condition'))
#         addConditionButton.Bind(wx.EVT_BUTTON, self.onAddCondition)
#         s = wx.BoxSizer(wx.HORIZONTAL)
#         s.Add(addConditionButton)
#         self.gridSizer.Add(s, (self.usedGridRows, 0), (1, 3))
#         self.usedGridRows = (self.usedGridRows + 1)
#         # add new-style condition panel
#         self.gridSizer.Add(self.getConditionPanel(self), (self.usedGridRows, 0), (1, 3))
        # set overall sizer
        self.SetSizer(self.gridSizer)
        self.gridSizer.Layout()
        # import filter conditions
        Logger.debug('MediaFilterPane.setModel(): setting up filter')
        self.importAndDisplayFilter()
        Logger.debug('MediaFilterPane.setModel() finished')


    def addCondition(self, aFilterCondition):
        """Add a new condition to self.
        
        Add the controls to the filter pane, make values settable and retrievable.
        
        Return a Number used as index to set and retrieve filter values.
        """
        conditionIndex = (len(self.filterConditions) + 1)
        self.filterConditions[conditionIndex] = aFilterCondition
        aFilterCondition.setCollectionModel(self.imageModel)
        aFilterCondition.setFilterModel(self.filterModel)
        # add filter controls
        self.gridSizer.Add(wx.StaticText(self, -1, (aFilterCondition.getLabel() + ':')), (self.usedGridRows, 0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        controls = aFilterCondition.getConditionControls()
        controlColumn = 1
        for control in controls:
            self.gridSizer.Add(control, (self.usedGridRows, controlColumn), flag=wx.ALIGN_CENTER_VERTICAL)
            controlColumn = (controlColumn + 1)
        self.usedGridRows = (self.usedGridRows + 1)
        return(conditionIndex)


    def addSeparator(self):
        """Add a separating whitespace to the filter list
        """
        self.gridSizer.Add((20, 20), (self.usedGridRows, 0), (1, 1))
        self.usedGridRows = (self.usedGridRows + 1)



# Getters
    def getFilterModel(self):
        return(self.filterModel)


#     def getCondition(self, filterRow):
#         """Return the controls registered under filterRow.
#         
#         Use this to set and retrieve values for the filter condition.
#         """
#         pass


#     def getPopupMenu(self):
#         """Return a wx.PopupMenu with filter choices.
#         """
#         if (self.popupMenu == None):
#             self.constructFilterConditionMap()
#         return(self.popupMenu)


# Event Handlers
#     def onAddConditionPopup(self, event):  # @UnusedVariable  # TODO: remove name part "Popup"
#         self.PopupMenu(self.getPopupMenu())


#     def onAddConditionSelected(self, event):
#         actionId = event.GetId()
#         self.filterConditionMap[actionId]()


#     def onAddCondition(self, event):  # @UnusedVariable
#         """
#         """
#         dialog = ConditionSelectionDialog(self, self.imageModel)
#         if (dialog.ShowModal() == wx.ID_OK):
#             print('Condition selected')
#         else:
#             print('nuffin!')
#         dialog.Destroy()


    def onClear(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        self.filterModel.clear()
        wx.EndBusyCursor()


    def onActivate(self, event):
        with wx.GetApp() as progressIndicator:  # @UnusedVariable
            self.filterModel.setConditions(active=event.GetEventObject().GetValue())  # TODO: acccept progressIndicator
            self.setActivateButtonText()


    def onModeChanged(self, event):  # @UnusedVariable
        """User changed a mode. Update filter. 
        """
        wx.BeginBusyCursor()
        kwargs = {}  # parameter set to pass to MediaFilter.setConditions()
        requiredTags = set()
        prohibitedTags = set()
        # for all classes, set up value filters
        for className in self.imageModel.getClassHandler().getClassNames():
            modeName = self.filterModes[className].GetStringSelection()
            valueName = self.filterValues[className].GetStringSelection()
            if (modeName == self.FilterModeNameRequire):
                if (valueName == self.FilterElementValuesAnyString):
                    requiredTags.add(className)
                else:
                    requiredTags.add(valueName)
            elif (modeName == self.FilterModeNameExclude):
                if (valueName == self.FilterElementValuesAnyString):
                    prohibitedTags.add(className)
                else:
                    prohibitedTags.add(valueName)
            else:  # must be 'ignore'
                pass
        kwargs['required'] = requiredTags
        kwargs['prohibited'] = prohibitedTags
        self.filterModel.setConditions(**kwargs)
        wx.EndBusyCursor()


    def onValueChanged(self, event):
        """User changed an element value in filter. Update internal state.
        
        In addition to the regular update done in onModeChanged(), 
        the mode corresponding to the value is set to Require if it was Ignore.
        """
        for key in self.filterValues:
            if (self.filterValues[key] == event.GetEventObject()):
                if (self.filterModes[key].GetStringSelection() == self.FilterModeNameIgnore):
                    Logger.debug('MediaFilterPane.onValueChanged(): Setting %s to required' % key)
                    self.filterModes[key].SetStringSelection(self.FilterModeNameRequire)
        return(self.onModeChanged(event))



# Inheritance - Observer
    def updateAspect(self, observable, aspect):  # @UnusedVariable
        """ ASPECT of OBSERVABLE has changed. 
        """
        if (aspect == 'changed'):
            self.importAndDisplayFilter()



# Internal
    def setActivateButtonText(self):
        if (self.activateButton.GetValue()):
            self.activateButton.SetLabel(_('Turn off filter'))
        else:
            self.activateButton.SetLabel(_('Turn on filter'))


    def addTextFilter(self, sizer, row, filterKey, label, control):
        '''Add a filter criterion to self, and insert the corresponding controls into self's Sizer.
        
        wx.GridBagSizer sizer  for layouting   
        Number row             the row to use in sizer
        String filterkey       index in self.filterValues[] map
        String label           the label of the condition
        wx.?? control          the control to enter the filter value (TextCtrl or Choice)
        Returns                -
        '''
        # filter label
        sizer.Add(wx.StaticText(self, -1, (label + ':')), (row, 0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # add control to specify value
        sizer.Add(control, (row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.filterValues[filterKey] = control
        # create choice of mode, linking to the value choice 
        modeChoice = wx.Choice(self, -1, choices=self.FilterModeNames)
        modeChoice.SetSelection(self.FilterModeIndexIgnore)
        self.filterModes[filterKey] = modeChoice
        sizer.Add(modeChoice, (row, 2), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHOICE, self.onModeChanged, modeChoice)


    def importAndDisplayFilter(self):
        """Redisplay criteria from self's filter. 
        """
        # TODO: import non-tag filters list media types, media size, etc.
        # TODO: do not reset tag selection when mode changes
        requiredElements = self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyRequired)
        if (requiredElements == None):
            requiredElements = set()
        prohibitedElements = self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyProhibited)
        if (prohibitedElements == None):
            prohibitedElements = set()
        # tags
        for className in self.imageModel.getClassHandler().getClassNames():
            # reset to no filtering
            self.filterModes[className].SetSelection(self.FilterModeIndexIgnore)
            self.filterValues[className].SetSelection(self.FilterModeIndexIgnore)
            if (className in requiredElements):
                self.filterModes[className].SetSelection(self.FilterModeIndexRequire)
                self.filterValues[className].SetStringSelection(self.FilterElementValuesAnyString)
            elif (className in prohibitedElements):
                self.filterModes[className].SetSelection(self.FilterModeIndexExclude)
                self.filterValues[className].SetStringSelection(self.FilterElementValuesAnyString)
            else:
                for element in self.imageModel.getClassHandler().getElementsOfClassByName(className):
                    if (element in requiredElements):
                        #print('Showing required "%s" in "%s"' % (element, className))
                        self.filterModes[className].SetSelection(self.FilterModeIndexRequire)
                        self.filterValues[className].SetStringSelection(element)
                    elif (element in prohibitedElements):
                        #print('Showing prohibited "%s" in "%s"' % (element, className))
                        self.filterModes[className].SetSelection(self.FilterModeIndexExclude)
                        self.filterValues[className].SetStringSelection(element)
        # button activation
        self.clearButton.Enable(enable=self.filterModel.isFiltering())



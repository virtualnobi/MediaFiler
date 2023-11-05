#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
from __future__ import print_function
import logging
import gettext
import os.path
import re
## Contributed
import wx
from wx.lib.scrolledpanel import ScrolledPanel
## nobi
from nobi.ObserverPattern import Observer
## Project
import UI  # to access UI.PackagePath
from UI import GUIId
#from Model.NewMediaFilter import ConditionTypeAnd, ConditionComplex, ConditionTag
from Model.MediaFilter import MediaFilter 
from Model.Installer import getFilterPath
from Model.NewMediaFilter import NewMediaFilter
#from Model.MediaClassHandler import MediaClassHandler



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.gettext
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class ConditionPane(wx.Panel):
    """A panel displaying a filter condition, containing information to recreate the entire filter
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, aFilterCondition):
        """
        """
        # inheritance
        wx.Panel.__init__(self, parent, style=(wx.FULL_REPAINT_ON_RESIZE))
        # internal state
        self.condition = aFilterCondition
        self.setupCondition()



# Setters
    # def setModel(self, anImageFilerModel):
    #     """Make anImageFilerModel the model of self, and create widgets on self accordingly.
    #     """


# Getters
    def getCondition(self):
        return(self.condition)



# Event Handlers
    # def onActivate(self, event):
    #     with wx.GetApp() as progressIndicator:  # @UnusedVariable
    #         self.filterModel.setConditions(active=event.GetEventObject().GetValue())
    #         self.defineActivateButtonText()


# Inheritance - Observer
    # def updateAspect(self, observable, aspect):  # @UnusedVariable
    #     """ ASPECT of OBSERVABLE has changed. 
    #     """
    #     if (aspect == 'changed'):
    #         self.setupConditions()



# Internal
    def setupCondition(self):
        """Set up self to display self.condition
        """
        wx.StaticText(self, -1, self.condition.getString())
        # self.SetSizerAndFit()
        # TODO: When using NewMediaFilter, do the following
        # if (isinstance(self.model, ConditionComplex)):
        #     wx.StaticBox(self, -1, self.model.getOperator())
        #     for condition in self.model.getSubconditions():
        #         panel = NewConditionPane(self, condition)
        # elif (isinstance(self.model, ConditionTag)):
        #     pass
        # elif (isinstance(self.model, MediaFilter)):  # TODO: make obsolete
        #     pass
        # else:
        #     raise ValueError('NewConditionPane.setupCondition(): Illegal type of parameter, expected Model.NewMediaFilter.Condition object!')



class ConditionRemovalButton(wx.Button):
    """A button to remove the associated condition from the filter.
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, number, conditionKey, widget):
        """Create a button to remove the widget in given number from filter.
        
        wx.Panel parent
        int number specifies the grid row in NewMediaFilterPane in which the button resides
        String conditionKey specifies the filter condition key 
        wx.Widget widget specifies which children of NewMediaFilterPane to remove
        """
        # inheritance
        wx.Button.__init__(self, parent, number, 'X')
        # internal state
        self.rowToDelete = number
        self.conditionKey = conditionKey
        self.widgetToDelete = widget
        # actions
        self.Bind(wx.EVT_BUTTON, self.onClick, self)



# Setters
    # def setModel(self, anImageFilerModel):
    #     """Make anImageFilerModel the model of self, and create widgets on self accordingly.
    #     """


# Getters
    def getWidgetToDelete(self):
        return(self.widgetToDelete)



# Event Handlers
    def onClick(self, event):
        print('Button X with id %s pressed' % event.GetId())
        self.GetParent().removeCondition(event.GetEventObject())



# Inheritance - Observer
    # def updateAspect(self, observable, aspect):  # @UnusedVariable
    #     """ ASPECT of OBSERVABLE has changed. 
    #     """
    #     if (aspect == 'changed'):
    #         self.setupConditions()
# Internal



class MediaFilterSaveDialog(wx.Dialog):
    """A dialog to enter a filename to store a NewMediaFilter to.
    """
    def __init__(self, parent, aNewMediaFilter):
        """
        """
        # inheritance
        super(MediaFilterSaveDialog, self).__init__(parent, -1, _('Save Filter'))
        # internal state
        self.filter = aNewMediaFilter
        # widgets
        dialogSizer = wx.BoxSizer(wx.VERTICAL)
        self.message = wx.StaticText(self, -1, '')  # error messages go here
        dialogSizer.Add(self.message, 0, (wx.EXPAND|wx.RIGHT|wx.TOP), 5)
        fieldSizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _('Filename:'))
        fieldSizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.text = wx.TextCtrl(self, -1, '', size=(80,-1))
        fieldSizer.Add(self.text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        dialogSizer.Add(fieldSizer, 0, wx.EXPAND|wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        dialogSizer.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.TOP, 5)
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        dialogSizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(dialogSizer)
        dialogSizer.Fit(self)


    def ShowModal(self):
        """
        """
        newFilterName = self.filter.getFilterName()
        if (not newFilterName):
            newFilterName = ''
        self.CenterOnScreen()
        done = False
        while (not done):
            self.text.SetValue(newFilterName)
            if (super(MediaFilterSaveDialog, self).ShowModal() == wx.ID_OK):
                newFilterName = self.text.GetValue()
                if (newFilterName == ''):
                    self.message.SetLabel(_('Name cannot be empty!'))
                elif ((newFilterName != self.filter.getFilterName())
                      and (newFilterName in MediaFilter.getUsedFilterNames())):
                    self.message.SetLabel(_('Name used in another filter!'))
                elif (not re.match(r'[a-zA-Z0-9._\-]+', newFilterName)):
                    self.message.SetLabel(_('Name contains illegal characters!'))
                else:  # finally, legal name
                    self.filter.setFilterName(newFilterName)
                    if (self.filter.saveFile()):
                        done = True 
                    else:
                        self.message.SetLabel(_('Could not save filter!'))
            else:
                done = True


    
class NewMediaFilterPane(ScrolledPanel, Observer):
    """A scrollable pane which visualizes the filter.
    """
# Constants
    MaximumFilterLevel = 5  # number of allowed embeddings in complex filter conditions (and, or, not)
    GridColumnLast = (MaximumFilterLevel + 1)  # column to display remove buttons for filter conditions
    ConditionTypeAndText = _('AND')
    ConditionTypeOrText = _('OR')
    ConditionTypeNotText = _('NOT')
    ConditionUnknownRequired = 'Unknown Tags Required'
    ConditionUnknownProhibited = 'Unknown Tags Prohibited'


# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, style=0, size=wx.Size(450,0)):
        """
        """
        # inheritance
        ScrolledPanel.__init__(self, parent, size=size, style=(style | wx.FULL_REPAINT_ON_RESIZE))
        # internal state
        self.imageModel = None
        self.filterName = ''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        # add button toolbar
        buttonToolbar = wx.BoxSizer(wx.HORIZONTAL)
        self.activateButton = wx.ToggleButton(self, -1, 'Filter')
        self.activateButton.Bind(wx.EVT_TOGGLEBUTTON, self.onActivate)
        self.defineActivateButtonText()
        buttonToolbar.Add(self.activateButton, 0, wx.EXPAND)
        self.clearButton = wx.Button(self, id=GUIId.ClearFilter, label=GUIId.FunctionNames[GUIId.ClearFilter])
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear, id=GUIId.ClearFilter)
        buttonToolbar.Add(self.clearButton, 0, wx.EXPAND)
        self.saveButton = wx.Button(self, id=GUIId.SaveFilter, label=_('Save'))
        self.saveButton.Bind(wx.EVT_BUTTON, self.onSave, id=GUIId.SaveFilter)
        buttonToolbar.Add(self.saveButton, 0, wx.EXPAND)
        self.loadButton = wx.Button(self, id=GUIId.LoadFilter, label=_('Load'))
        self.loadButton.Bind(wx.EVT_BUTTON, self.onLoad, id=GUIId.LoadFilter)
        buttonToolbar.Add(self.loadButton, 0, wx.EXPAND)
        self.GetSizer().Add(buttonToolbar)
        self.GetSizer().Add((10, 10))
        self.GetSizer().Add(wx.GridBagSizer())
        self.filterWidgets = []  # these need to be discarded when the filter model changes
        # self.conditionPane = ScrolledPanel(self, -1, style=(wx.TAB_TRAVERSAL))
        # self.conditionPane.SetAutoLayout(1)
        # self.conditionPane.SetupScrolling()        
        # self.GetSizer().Add(self.conditionPane)
        self.SetAutoLayout(1)
        self.SetupScrolling()        
        self.GetSizer().Layout()



# Setters
    def setModel(self, anImageFilerModel):
        """Make anImageFilerModel the model of self, and create widgets on self accordingly.
        """
        Logger.debug('NewMediaFilterPane.setModel(')
        self.clearModel()
        self.imageModel = anImageFilerModel
#         self.imageModel.addObserverForAspect(self, 'filterChanged')  # TODO: add this aspect to MediaCollection
        self.getFilterModel().addObserverForAspect(self, 'changed')  # TODO: if above is done, this is obsolete
        self.setupConditions()  # adds conditions to self.conditionPane
        self.GetSizer().Layout()
        Logger.debug('NewMediaFilterPane.setModel() finished')


# Getters
    def getModel(self):
        return self.imageModel


    def getFilterModel(self):
        return self.getModel().getFilter()



# Event Handlers
    def onActivate(self, event):
        wx.BeginBusyCursor()
        with wx.GetApp() as progressIndicator:  # @UnusedVariable
            self.getFilterModel().setConditions(active=event.GetEventObject().GetValue())
            self.defineActivateButtonText()
        wx.EndBusyCursor()


    def onClear(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        with wx.GetApp() as progressIndicator:  # @UnusedVariable
            self.getFilterModel().clear()
        wx.EndBusyCursor()


    def onSave(self, event):  # @UnusedVariable
        """User wants to save filter.
        
        Save filter to the file with the known filter name.
        """
        dialog = MediaFilterSaveDialog(self, self.getFilterModel())
        dialog.ShowModal()  # includes saving the filter
        self.saveButton.Disable()
        dialog.Destroy()


    def onLoad(self, event):  # @UnusedVariable
        """User wants to load filter.
        
        Ask user to select a file from filters directory,
        then load the filter described in this file and activate it.
        
        TODO: Create a subclass of SingleChoiceDialog which allows to delete and rename the filters. 
        TODO: Add an easy reload function (either special button or preselecting current filter).
        """
        filters = MediaFilter.getUsedFilterNames()
        currentFilter = self.getFilterModel().getFilterName()
        if (currentFilter):
            filters = (filters - set(currentFilter))
        dlg = wx.SingleChoiceDialog(self, _('Pick one of the existing filters.'), _('Load Filter'), list(filters), wx.CHOICEDLG_STYLE)
        if (dlg.ShowModal() == wx.ID_OK):
            newFilterName = dlg.GetStringSelection()
            Logger.debug('You selected: %s\n' % newFilterName)
            wx.BeginBusyCursor()
            self.getFilterModel().loadFromFile(os.path.join(getFilterPath(), newFilterName))
            self.getFilterModel().setConditions(active=True)
            self.saveButton.Disable()
            wx.EndBusyCursor()
        dlg.Destroy()


    def onConditionChanged(self, event):  # @UnusedVariable
        """User changed a filter condition. Update filter to show changed media. 
        """
        wx.BeginBusyCursor()
        wx.EndBusyCursor()



# Inheritance - Observer
    def updateAspect(self, observable, aspect):  # @UnusedVariable
        """ ASPECT of OBSERVABLE has changed. 
        """
        if (aspect == 'changed'):
            wx.BeginBusyCursor()
            self.setupConditions()
            wx.EndBusyCursor()



# Internal
    def clearModel(self):
        """Release all data related to the model, including widgets
        """
        # clear dependencies
        try: 
            self.imageModel.removeObserver(self)
        except: 
            pass
        self.imageModel = None
        # clear widgets
        # for child in self.conditionPane.GetChildren():
        for child in self.filterWidgets:
            Logger.debug('NewMediaFilterPane.clearModel(): Detaching and destroying %s' % child)
            self.GetSizer().Detach(child)
            child.Destroy()
        # self.conditionPane.DestroyChildren()
        # self.conditionPane.SetSizer(wx.GridBagSizer())
        self.filterWidgets = []
        self.GetSizer().Layout()
        # clear internal state


    def setCurrentGridRow(self, number):
        self.currentGridRow = number


    def setCurrentGridColumn(self, number):
        self.currentGridColumn = number


    def getCurrentGridRow(self):
        return self.currentGridRow


    def getCurrentGridColumn(self):
        return self.currentGridColumn


    def setupConditions(self):
        """Add the conditions from the filter to self.conditionPane
        """
        Logger.debug('NewMediaFilterPane.setupConditions(')
        # activation
        self.activateButton.SetValue(self.getFilterModel().isActive())
        self.defineActivateButtonText()
        # filter's dirty state determines save button enablement
        if (self.getFilterModel().isSaved()):
            self.saveButton.Disable()
        else:
            self.saveButton.Enable()
        # clear filter conditions, but leave toolbar intact
        for child in self.filterWidgets:
            Logger.debug('NewMediaFilterPane.setupConditions(): Trying to remove %s' % child)
            self.GetSizer().Detach(child)
            child.Destroy()
        self.filterWidgets = []
        self.GetSizer().Remove(2)
        self.conditionGrid = wx.GridBagSizer()
        self.setCurrentGridRow(1)
        self.setCurrentGridColumn(1)
        # first, show filter name, if any
        text = wx.StaticText(self, -1, ('Filter Name = "%s"' % self.getFilterModel().getFilterName()))
        self.filterWidgets.append(text)
        self.conditionGrid.Add(text, (self.getCurrentGridRow(), 1), (1, NewMediaFilterPane.MaximumFilterLevel))
        self.setCurrentGridRow(self.getCurrentGridRow() + 1)
        # to represent old-style MediaFilter, automatically wrap AND around its conditions
        text = wx.StaticText(self, -1, NewMediaFilterPane.ConditionTypeAndText)
        self.filterWidgets.append(text)
        self.conditionGrid.Add(text, (self.getCurrentGridRow(), 1), (1, NewMediaFilterPane.MaximumFilterLevel))
        self.setCurrentGridRow(self.getCurrentGridRow() + 1)
        self.conditionGrid.Add((10,10), (self.getCurrentGridRow(), self.getCurrentGridColumn()), (1, 1))
        self.setCurrentGridColumn(self.getCurrentGridColumn() + 1)
        # required tags
        tags = self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyRequired)
        tags = tags.union(self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired))
        Logger.debug('NewMediaFilterPane.setupConditions(): Required tags are %s' % tags)
        for tag in tags:
            if (self.imageModel.getClassHandler().isLegalElement(tag)):
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding tag %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Tag %s required') % tag)
                # text = wx.StaticText(self, -1, _('Tag %s required') % tag)
            elif (tag in self.imageModel.getClassHandler().getClassNames()): 
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding class %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Class %s required') % tag)
                # text = wx.StaticText(self, -1, _('Class %s required') % tag)
            else:  # must be unknown 
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding unknown %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Unknown tag %s required') % tag)
            #     text = wx.StaticText(self, -1, _('Unknown tag %s required') % tag)
            # self.filterWidgets.append(text)
            # self.conditionGrid.Add(text, (self.getCurrentGridRow(), self.getCurrentGridColumn()), (1, (NewMediaFilterPane.MaximumFilterLevel - self.getCurrentGridColumn())))
            # self.setCurrentGridRow(self.getCurrentGridRow() + 1)
        # prohibited tags
        tags = self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyProhibited)
        tags = tags.union(self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited))
        Logger.debug('NewMediaFilterPane.setupConditions(): Excluded tags are %s' % tags)
        for tag in tags: 
            if (self.imageModel.getClassHandler().isLegalElement(tag)):
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding tag %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Tag %s excluded') % tag)
            elif (tag in self.imageModel.getClassHandler().getClassNames()): 
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding class %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Class %s excluded') % tag)
            else:  # must be unknown 
                Logger.debug('NewMediaFilterPane.setupConditions(): Adding unknown %s on row %s' % (tag, self.getCurrentGridRow()))
                self.addCondition(_('Unknown tag %s excluded') % tag)
        # required unknowns
        if (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyUnknownRequired)):
            self.addCondition(NewMediaFilterPane.ConditionUnknownRequired)
        # prohibited unknowns
        if (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited)):
            self.addCondition(NewMediaFilterPane.ConditionUnknownProhibited)
        # type restrictions
        for requiredType in self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyMediaTypesRequired):
            conditionString = (_('Type "%s" required') % requiredType.getMediaTypeName())
            self.addCondition(conditionString)
        # size restrictions
        conditionString = None
        if (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum)):
            if (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum)):
                conditionString = (_('Resolution between %s%% and %s%%') % (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum), 
                                                                            self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum)))
            else:
                conditionString = (_('Resolution larger than %s%%') % self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum))
        elif (self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum)):
            conditionString = (_('Resolution smaller than %s%%') % self.getFilterModel().getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum))
        if (conditionString):
            self.addCondition(conditionString)
        # organization-specific conditions
        for c in self.imageModel.organizationStrategy.conditionsFromFilter(self, self.getFilterModel()):
            self.addCondition(c)
        self.GetSizer().Add(self.conditionGrid)
        self.GetSizer().Layout()
        Logger.debug('NewMediaFilterPane.setupConditions(): Done')


    def addCondition(self, stringOrWidget):
        """Add a new condition to self.
        
        When passing a string as widget, a StaticText showing the string is added.
        
        String|wx.Widget stringOrWidget specifies the control to add 
        """
        if (isinstance(stringOrWidget, str)):
            widget = wx.StaticText(self, -1, stringOrWidget)
        else:
            widget = stringOrWidget
        self.filterWidgets.append(widget)
        self.conditionGrid.Add(widget, (self.getCurrentGridRow(), self.getCurrentGridColumn()), (1, (NewMediaFilterPane.MaximumFilterLevel - self.getCurrentGridColumn())))
        removeButton = ConditionRemovalButton(self, self.getCurrentGridRow(), '', widget)
        self.filterWidgets.append(removeButton)
        self.conditionGrid.Add(removeButton, (self.getCurrentGridRow(), NewMediaFilterPane.MaximumFilterLevel), (1,1))
        self.setCurrentGridRow(self.getCurrentGridRow() + 1)


    def removeCondition(self, widget):
        """Remove the filter condition represented by a given widget, from the filter as well as the UI.
        
        wx.Control widget
        """
        # remove condition from filter
        self.getFilterModel().removeConditionKey('')
        # remove widget from filter pane TODO: this should be done automagically when changing the filter
        self.filterWidgets.remove(widget)
        self.filterWidgets.remove(widget.getWidgetToDelete())
        self.conditionGrid.Remove(widget)
        self.conditionGrid.Remove(widget.getWidgetToDelete())
        self.conditionGrid.Layout()
    

    def defineActivateButtonText(self):
        if (self.activateButton.GetValue()):
            self.activateButton.SetLabel(_('Turn off'))
        else:
            self.activateButton.SetLabel(_('Turn on'))



# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



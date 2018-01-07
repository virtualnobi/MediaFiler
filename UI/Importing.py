"""
Classes to support the importing of media.

(c) by nobisoft 2016-
"""


# Imports
## Standard
import gettext
import os.path
import StringIO
import logging
## Contributed
import wx
## nobi
## Project
from Model import GlobalConfigurationOptions
from Model.MediaClassHandler import MediaClassHandler
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.MediaOrganization.OrganizationByName import OrganizationByName
from Model.MediaOrganization.OrganizationByDate import OrganizationByDate



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.normpath(os.path.join(UI.PackagePath, '..', 'locale'))
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



class ImportParameterObject(object):
    """A ParameterObject pattern to collect import control parameters.
    
    For a complete list of parameters and their default values, see __init__()
    """



# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, model):
        """
        """
        # inheritance
        super(ImportParameterObject, self).__init__()
        # internal state
        self.model = model
        self.log = StringIO.StringIO()
        self.illegalElements = {}
        self.testRun = True
        self.numberOfImportedFiles = 0
        # the following are options on the UI, which are defaulted to last used values
        self.importDirectory = self.model.getConfiguration(GlobalConfigurationOptions.ImportPath)
        if (self.importDirectory == None):
            self.importDirectory = os.path.normpath(os.path.join(self.model.getRootDirectory(), '..', 'import'))
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportIgnoreUnhandled)
        if (stringValue == None):
            self.ignoreUnhandledTypes = (self.model.organizationStrategy == OrganizationByName)
        else: 
            self.ignoreUnhandledTypes = (stringValue == 'True')
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportMinimumSize)
        if (stringValue == None):
            self.minimumFileSize = 10000
        else:
            self.minimumFileSize = int(stringValue)
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportDeleteOriginals)
        if (stringValue == None):
            self.deleteOriginals = True
        else: 
            self.deleteOriginals = (stringValue == 'True')
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportMarkAsNew)
        if (stringValue == None):
            self.markAsNew = True
        else: 
            self.markAsNew = (stringValue == 'True')
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportMaximumFiles)
        if (stringValue == None):
            self.maxFilesToImport = 1000
        else:
            self.maxFilesToImport = int(stringValue)
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportKeepUnknownTags)
        if (stringValue == None):
            self.keepUnknownTags = (self.model.organizationStrategy == OrganizationByDate)
        else:
            self.keepUnknownTags = (stringValue == 'True')                    
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportReportIllegals)
        if (stringValue == None):
            self.reportIllegalElements = False
        else: 
            self.reportIllegalElements = (stringValue == 'True')            
        # parameters for OrganizationByDate
        stringValue = self.model.getConfiguration(GlobalConfigurationOptions.ImportPreferExif)
        if (stringValue == None):
            self.preferPathDateOverExifDate = True
        else: 
            self.preferPathDateOverExifDate = (stringValue == 'True')
        # parameters for OrganizationByName
        return(None)



# Setters
    def setImportDirectory(self, value):
        self.importDirectory = value


    def setTestRun(self, value):
        self.testRun = value        


    def setIgnoreUnhandledTypes(self, value):
        self.ignoreUnhandledTypes = value


    def setMinimumFileSize(self, value):
        self.minimumFileSize = value


    def setDeleteOriginals(self, value):
        self.deleteOriginals = value
    
    
    def setMarkAsNew(self, value):
        self.markAsNew= value


    def setMaxFilesToImport(self, value):
        self.maxFilesToImport = value
        self.numberOfImportedFiles = 0


    def setReportIllegalElements(self, value):
        self.reportIllegalElements = value


    def setPreferPathDateOverExifDate(self, value):
        self.preferPathDateOverExifDate = value


    def setKeepUnknownTags(self, value):
        self.keepUnknownTags = value


    def logString(self, strng):
        self.log.write(strng)
        self.log.write('\n')


# Getters
    def getImportDirectory(self):
        return(self.importDirectory)


    def getTestRun(self):
        return(self.testRun)


    def getIgnoreUnhandledTypes(self):
        return(self.ignoreUnhandledTypes)


    def getMinimumFileSize(self):
        return(self.minimumFileSize)


    def getDeleteOriginals(self):  
        return(self.deleteOriginals)


    def getMarkAsNew(self):
        return(self.markAsNew)


    def getMaxFilesToImport(self):
        return(self.maxFilesToImport)


    def getReportIllegalElements(self):
        return(self.reportIllegalElements)


    def getPreferPathDateOverExifDate(self):
        return(self.preferPathDateOverExifDate)


    def getLog(self):
        return(self.log.getvalue())


    def getNumberOfImportedFiles(self):
        return(self.numberOfImportedFiles)


    def canImportOneMoreFile(self):
        """One more file has been imported - is the maximum number reached?
        
        Return Boolean indicating whether import can continue
        """
        self.numberOfImportedFiles = (self.numberOfImportedFiles + 1)
        return(self.numberOfImportedFiles <= self.maxFilesToImport)


    def getKeepUnknownTags(self):
        return(self.keepUnknownTags)


# Other API functions
    def storeSettings(self):
        """User has accepted the settings to import media. Store them for next use.
        """
        self.model.setConfiguration(GlobalConfigurationOptions.ImportPath, 
                                    self.importDirectory)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportIgnoreUnhandled,
                                    self.ignoreUnhandledTypes)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportMinimumSize,
                                    self.minimumFileSize)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportDeleteOriginals,
                                    self.deleteOriginals)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportMarkAsNew,
                                    self.markAsNew)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportMaximumFiles,
                                    self.maxFilesToImport)
        self.model.setConfiguration(GlobalConfigurationOptions.ImportKeepUnknownTags,
                                    self.keepUnknownTags)        
        self.model.setConfiguration(GlobalConfigurationOptions.ImportReportIllegals,
                                    self.reportIllegalElements)
        # parameters for OrganizationByDate
        self.model.setConfiguration(GlobalConfigurationOptions.ImportPreferExif,
                                    self.preferPathDateOverExifDate)
        # parameters for OrganizationByName



# Event Handlers
# Internal - to change without notice
# Class Initialization




class ImportDialog(wx.Dialog): 
    """A wx.Dialog asking for all relevant information to import a directory.
    
    The parameters collected to control the import process are available as a ImportParameters object. 
    """
    

# Constants
    Logger = logging.getLogger(__name__)
    # dialog texts
    TitleTestRun = _('Test Import')
    TitleImport = _('Import')
    FieldLabelImportDirectory = _('Directory')
    FieldLabelTestRun = _('Test Only')
    FieldLabelDeleteOriginal = _('Delete Originals')
    FieldLabelMaxNumber = _('Maximum Number of Files to Import')
    FieldLabelIgnoreUnknowns = _('Ignore Files of Unknown Type')
    FieldLabelMinimumSize = _('Minimum File Size')
    FieldLabelMarkAsNew = (_('Mark Imported Files as "%s"') % MediaClassHandler.ElementNew)
    FieldLabelKeepUnknown = _('Keep Unknown Tags')
    FieldLabelReportIllegal = _('Report Illegal Elements')
    FieldLabelPreferPathDate = _('Prefer Date in Pathname over EXIF Date')



# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, model, parameters,
                 size=wx.DefaultSize, 
                 pos=wx.DefaultPosition, 
                 style=(wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)):
        """Create and return a new ImportDialog.
        """
        # internal state
        self.parameters = parameters
        if (parameters.getTestRun()):
            title = self.TitleTestRun
        else:
            title = self.TitleImport
        # inheritance
        super(ImportDialog, self).__init__(parent, id=-1, title=title, size=size, pos=pos, style=style)
        s = wx.GridBagSizer(9, 8)
        # row 1 - import directory
        vBox = wx.BoxSizer()
        self.importDirectoryField = wx.TextCtrl(self, size=(200,0))
        self.importDirectoryField.SetValue(self.parameters.getImportDirectory())
        self.Bind(wx.EVT_TEXT, self.onDirectoryChanged, self.importDirectoryField)
        vBox.Add(self.importDirectoryField, flag=(wx.EXPAND|wx.ALIGN_CENTER_VERTICAL))
        self.importDirectoryBrowseButton = wx.Button(self, GUIId.BrowseImportDirectory)
        self.importDirectoryBrowseButton.SetLabel(GUIId.FunctionNames[GUIId.BrowseImportDirectory])
        self.Bind(wx.EVT_BUTTON, self.onBrowse, self.importDirectoryBrowseButton)
        vBox.Add(self.importDirectoryBrowseButton, flag=wx.ALIGN_CENTER_VERTICAL)
        s.Add(vBox,
              (0, 0),
              (1, 2),
              (wx.ALIGN_CENTER_VERTICAL|wx.EXPAND))
        # row 2 - separator
        s.Add(wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL), 
              (1, 0),
              (1, 2), 
              (wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP|wx.EXPAND))
        # row 3 - deleteOriginals
        s.Add(wx.StaticText(self, -1, self.FieldLabelDeleteOriginal),
              (2, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        checkbox = wx.CheckBox(self)
        if (self.parameters.getTestRun()):
            checkbox.SetValue(False)
            checkbox.Enable(False)
        else:
            checkbox.SetValue(self.parameters.getDeleteOriginals())
            checkbox.Enable(True)
        self.Bind(wx.EVT_CHECKBOX, self.onDeleteOriginal, checkbox)
        s.Add(checkbox, 
              (2, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 4 - ignoreUnknownTypes
        s.Add(wx.StaticText(self, -1, self.FieldLabelIgnoreUnknowns),
              (3, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.parameters.getIgnoreUnhandledTypes())
        self.Bind(wx.EVT_CHECKBOX, self.onIgnoreUnknowns, checkbox)
        s.Add(checkbox, 
              (3, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 5 - maxFilesToImport
        s.Add(wx.StaticText(self, -1, self.FieldLabelMaxNumber),
              (4, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        textField = wx.TextCtrl(self, -1, '', size=(125, -1))
        textField.SetValue(str(self.parameters.getMaxFilesToImport()))
        self.Bind(wx.EVT_TEXT, self.onMaxNumber, textField)
        s.Add(textField, 
              (4, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 6 - minimumFileSize
        s.Add(wx.StaticText(self, -1, self.FieldLabelMinimumSize),
              (5, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        textField = wx.TextCtrl(self, -1, '', size=(125, -1))
        textField.SetValue(str(self.parameters.getMinimumFileSize()))
        self.Bind(wx.EVT_TEXT, self.onMinimumSize, textField)
        s.Add(textField, 
              (5, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 7 - markAsNew
        s.Add(wx.StaticText(self, -1, self.FieldLabelMarkAsNew),
              (6, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.parameters.getMarkAsNew())
#        checkbox.Enable(model.organizedByDate)
        self.Bind(wx.EVT_CHECKBOX, self.onMarkAsNew, checkbox)
        s.Add(checkbox, 
              (6, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 8 - keepUnknownTags
        s.Add(wx.StaticText(self, -1, self.FieldLabelKeepUnknown),
              (7, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)) 
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.parameters.getKeepUnknownTags())
        self.Bind(wx.EVT_CHECKBOX, self.onKeepUnknown, checkbox)
        s.Add(checkbox, 
              (7, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 9 - reportIllegalElements
        s.Add(wx.StaticText(self, -1, self.FieldLabelReportIllegal),
              (8, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)) 
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.parameters.getReportIllegalElements())
        self.Bind(wx.EVT_CHECKBOX, self.onReportIllegal, checkbox)
        s.Add(checkbox, 
              (8, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 10 - preferPathDateOverExifDate
        if (model.organizedByDate):
            s.Add(wx.StaticText(self, -1, self.FieldLabelPreferPathDate),
                  (9, 0),
                  (1, 1),
                  (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)) 
            checkbox = wx.CheckBox(self)
            checkbox.SetValue(self.parameters.getPreferPathDateOverExifDate())
            self.Bind(wx.EVT_CHECKBOX, self.onPreferPathDate, checkbox)
            s.Add(checkbox, 
                  (9, 1),
                  (1, 1),
                  (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 11 - buttons
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn) 
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize() 
        s.Add(btnsizer, 
              (10, 0),
              (1,2), 
              (wx.ALIGN_RIGHT|wx.ALL))
        # events
        self.Bind(wx.EVT_SIZING, self.onResize)
        # fit sizer
        self.SetSizerAndFit(s)
        self.SetAutoLayout(True)
        return(None)



# Setters
# Getters
    def getParameterObject(self):
        return(self.parameters)



# Event Handlers
    def onResize(self, event):  # @UnusedVariable
        #event.GetEventObject().GetSizer().Layout()
        self.__class__.Logger.warning('ImportDialog.onResize(): Resize event ignored')


    def onDirectoryChanged(self, event):  # @UnusedVariable
        self.parameters.setImportDirectory(self.importDirectoryField.GetValue())
        self._class__.Logger.debug('ImportDialog.onDirectoryChanged(): importDirectory set to %s' % self.parameters.getImportDirectory())


    def onBrowse(self, event):  # @UnusedVariable
        """User wants to browse for a new import directory
        """
        if (self.parameters.getTestRun()):
            dialogTitle = _("Choose a directory to test import:")
        else:
            dialogTitle = _("Choose a directory to import from:")
        dirDialog = wx.DirDialog(self, dialogTitle, style = (wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST))
        dirDialog.SetPath(self.parameters.getImportDirectory())  # TODO: expand and scroll to this directory
        if (dirDialog.ShowModal() == wx.ID_OK):  
            self.parameters.setImportDirectory(dirDialog.GetPath())
            self.importDirectoryField.SetValue(self.parameters.getImportDirectory())
        dirDialog.Destroy()


    def onDeleteOriginal(self, event):
        self.parameters.setDeleteOriginals(event.GetEventObject().GetValue())
        self._class__.Logger.debug('ImportDialog.onDeleteOriginal(): deleteOriginals set to %s' % self.parameters.getDeleteOriginals())


    def onMaxNumber(self, event):
        try:
            maxFiles = int(event.GetEventObject().GetValue())
        except:
            pass
        else:
            self.parameters.setMaxFilesToImport(maxFiles)
            self._class__.Logger.debug('ImportDialog.onMaxNumber(): maxFilesToImport set to %s' % self.parameters.getMaxFilesToImport())


    def onIgnoreUnknowns(self, event):
        self.parameters.setIgnoreUnhandledTypes(event.GetEventObject().GetValue())
        self._class__.Logger.debug('ImportDialog.onIgnoreUnknowns(): ignoreUnknowns set to %s' % self.parameters.getIgnoreUnhandledTypes())


    def onMarkAsNew(self, event):
        self.parameters.setMarkAsNew(event.GetEventObject().GetValue())
        self._class__.Logger.debug('ImportDialog.onMarksAsNew(): markAsNew set to %s' % self.parameters.getMarkAsNew())

    
    def onMinimumSize(self, event):
        string = event.GetEventObject().GetValue()
        try: 
            size = int(string)
        except: 
            event.GetEventObject().SetValue(self.parameters.getMinimumFileSizeAsString())
        else:
            self.parameters.setMinimumFileSize(size)
            self._class__.Logger.debug('ImportDialog.onMinimumSize set to %s' % self.parameters.getMinimumFileSize())


    def onKeepUnknown(self, event):
        """
        """
        self.parameters.setKeepUnknownTags(event.GetEventObject().GetValue())
        self.__class__.Logger.debug('ImportDialog.onKeepUnknown(): keepUnknownTags set to %s' % self.parameters.getKeepUnknownTags())


    def onReportIllegal(self, event):
        """
        """
        self.parameters.setReportIllegalElements(event.GetEventObject().GetValue())
        self._class__.Logger.debug('ImportDialog.onReportIllegal(): reportIllegals set to %s' % self.parameters.getReportIllegalElements())


    def onPreferPathDate(self, event):
        """
        """
        self.parameters.setPreferPathDateOverExifDate(event.GetEventObject().GetValue())
        self._class__.Logger.debug('ImportDialog.onPreferPathDate(): preferPathDate set to %s' % self.parameters.getPreferPathDateOverExifDate())



# Other API Functions
    def ShowModal(self):
        """In addition to superclass, store parameter settings if user hits OK.
        """
        result = super(ImportDialog, self).ShowModal()
        if (result == wx.ID_OK):
            self.parameters.storeSettings()
        return(result)



# Internal - to change without notice
# Class Initialization



# Executable Script
if __name__ == "__main__":
    pass


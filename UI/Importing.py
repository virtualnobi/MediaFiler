"""
Classes to support the importing of media.

(c) by nobisoft 2016-
"""


# Imports
## Standard
import gettext
import os.path
import StringIO
## Contributed
import wx
## nobi
## Project
from Model.MediaClassHandler import MediaClassHandler
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.Organization import OrganizationByName



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.normpath(os.path.join(UI.PackagePath, '..', 'locale'))
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
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
    @classmethod
    def classMethod(clas):
        """
        """
        pass



# Lifecycle
    def __init__(self, model):
        """
        """
        # inheritance
        super(ImportParameterObject, self).__init__()
        # internal state
        self.log = StringIO.StringIO()
        self.illegalElements = {}
        self.importDirectory = os.path.normpath(os.path.join(model.getRootDirectory(), '..', 'import'))
        self.testRun = True
        self.ignoreUnhandledTypes = (model.organizationStrategy == OrganizationByName)
        self.minimumFileSize = 10000
        self.deleteOriginals = True
        self.markAsNew = True
        self.maxFilesToImport = 1000
        self.numberOfImportedFiles = 0
        self.reportIllegalElements = False
        # parameters for OrganizationByDate
        self.preferPathDateOverExifDate = True
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



# Event Handlers
# Internal - to change without notice
# Class Initialization




class ImportDialog(wx.Dialog): 
    """A wx.Dialog asking for all relevant information to import a directory.
    
    The parameters collected to control the import process are available as a ImportParameters object. 
    """
    

# Constants
    TitleTestRun = _('Test Import')
    TitleImport = _('Import')
    FieldLabelImportDirectory = _('Directory')
    FieldLabelTestRun = _('Test Only')
    FieldLabelDeleteOriginal = _('Delete Originals')
    FieldLabelMaxNumber = _('Maximum Number of Files to Import')
    FieldLabelIgnoreUnknowns = _('Ignore Files of Unknown Type')
    FieldLabelMinimumSize = _('Minimum File Size')
    FieldLabelMarkAsNew = (_('Mark Imported Files as "%s"') % MediaClassHandler.ElementNew)
    FieldLabelReportIllegal = _('Report Illegal Elements')
    FieldLabelPreferPathDate = _('Prefer Date in Pathname over EXIF Date')



# Class Variables
# Class Methods
    @classmethod
    def classMethod(clas):
        """
        """
        pass



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
        s = wx.GridBagSizer(8, 8)
        # row 1 - import directory
        vBox = wx.BoxSizer()
        self.importDirectoryField = wx.TextCtrl(self, size=(200,0))
        self.importDirectoryField.SetValue(self.parameters.getImportDirectory())
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
        # row 8 - reportIllegalElements
        s.Add(wx.StaticText(self, -1, self.FieldLabelReportIllegal),
              (7, 0),
              (1, 1),
              (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)) 
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.parameters.getReportIllegalElements())
        self.Bind(wx.EVT_CHECKBOX, self.onReportIllegal, checkbox)
        s.Add(checkbox, 
              (7, 1),
              (1, 1),
              (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 9 - preferPathDateOverExifDate
        if (model.organizedByDate):
            s.Add(wx.StaticText(self, -1, self.FieldLabelPreferPathDate),
                  (8, 0),
                  (1, 1),
                  (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)) 
            checkbox = wx.CheckBox(self)
            checkbox.SetValue(self.parameters.getPreferPathDateOverExifDate())
            self.Bind(wx.EVT_CHECKBOX, self.onPreferPathDate, checkbox)
            s.Add(checkbox, 
                  (8, 1),
                  (1, 1),
                  (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        # row 10 - buttons
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn) 
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize() 
        s.Add(btnsizer, 
              (9, 0),
              (1,2), 
              (wx.ALIGN_RIGHT|wx.ALL))
        # events
        self.Bind(wx.EVT_SIZING, self.onResize)
        # fit sizer
        self.SetSizerAndFit(s)
        self.SetAutoLayout(True)
        return(None)



# Setters
    def setAttribute(self, value):
        """
        """
        pass
    
    

# Getters
    def getParameterObject(self):
        return(self.parameters)



# Event Handlers
    def onResize(self, event):  # @UnusedVariable
        """
        """
        #event.GetEventObject().GetSizer().Layout()
        print('Not Resizing')


    def onBrowse(self, event):  # @UnusedVariable
        """User wants to browse for a new import directory
        """
        #print('ImportDialog.onBrowse() here')
        # set up a few texts
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
        """
        """
        self.parameters.setDeleteOriginals(event.GetEventObject().GetValue())
        print('DeleteOriginals=%s' % self.parameters.getDeleteOriginals())


    def onMaxNumber(self, event):
        """
        """
        try:
            maxFiles = int(event.GetEventObject().GetValue())
        except:
            pass
        else:
            self.parameters.setMaxFilesToImport(maxFiles)
            print('MaxFilesToImport=%s' % self.parameters.getMaxFilesToImport())


    def onIgnoreUnknowns(self, event):
        """
        """
        self.parameters.setIgnoreUnhandledTypes(event.GetEventObject().GetValue())
        print('IgnoreUnknown=%s' % self.parameters.getIgnoreUnhandledTypes())


    def onMarkAsNew(self, event):
        """
        """
        self.parameters.setMarkAsNew(event.GetEventObject().GetValue())
        print('MarksAsNew=%s' % self.parameters.getMarkAsNew())

    
    def onMinimumSize(self, event):
        """
        """
        string = event.GetEventObject().GetValue()
        try: 
            size = int(string)
        except: 
            event.GetEventObject().SetValue(self.parameters.getMinimumFileSizeAsString())
        else:
            self.parameters.setMinimumFileSize(size)
            print('MinimumFileSize=%s' % self.parameters.getMinimumFileSize())


    def onReportIllegal(self, event):
        """
        """
        self.parameters.setReportIllegalElements(event.GetEventObject().GetValue())
        print('ReportIllegalElements=%s' % self.parameters.getReportIllegalElements())


    def onPreferPathDate(self, event):
        """
        """
        self.parameters.setPreferPathDateOverExifDate(event.GetEventObject().GetValue())
        print('PreferPathDate=%s' % self.parameters.getPreferPathDateOverExifDate())



# Internal - to change without notice
# Class Initialization



# Executable Script
if __name__ == "__main__":
    pass


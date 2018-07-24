'''(c) by nobisoft 2016-
'''


# Imports
## standard
#import sys
import os 
import subprocess
import gettext
import shutil
import shlex
import logging
#from logging import FileHandler
import time
import cProfile
import pstats
#import types
import pkgutil
## contributed
import wx.aui
import wx.lib.dialogs
## nobi
from nobi.ObserverPattern import Observable, Observer
from nobi.wx.ProgressSplashApp import ProgressSplashApp
## project
from Model import GlobalConfigurationOptions
from Model import Installer
from Model.MediaCollection import MediaCollection
from Model import Image  # @UnusedImport import even if "unused", otherwise it's never registered with Installer.ProductTrader
from Model import Movie  # @UnusedImport import even if "unused", otherwise it's never registered with Installer.ProductTrader  
import UI  # to access UI.PackagePath
from UI import GUIId
from UI.Importing import ImportDialog, ImportParameterObject
from UI.MediaFilterPane import MediaFilterPane
from UI.PresentationControlPane import PresentationControlPane
from UI.MediaTreePane import MediaTreeCtrl
from UI.MediaCanvasPane import MediaCanvas
from UI.MediaNamePane import MediaNamePane
from UI.MediaClassificationPane import MediaClassificationPane



# Internationalization
# requires "PackagePath = __path__[0]" in UI/_init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
    print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message



class MediaFiler(wx.Frame, Observer, Observable):   
    """A Python 2.7 GUI application which lets you organize media (images and videos). 
    """



# Constants
    PaneCaptionFilter = _('Filter')
    PaneCaptionImages = _('Media')
    PaneCaptionName = _('Name')
    PaneCaptionClassification = _('Classification')
    PaneCaptionLog = _('Log')
    PerspectiveIndexClassify = 0
    PerspectiveNameClassify = _('Classify')
    PerspectiveIndexFilter = 1
    PerspectiveNameFilter = _('Search')
    PerspectiveIndexPresent = 2
    PerspectiveNamePresent = _('Present')
    PerspectiveIndexAll = 3
    PerspectiveNameAll = _('All Views')
    PerspectiveNameLastUsed = _('Last Used')
    MenuTitleFile = _('&Program')
    MenuTitleImage = _('&Media')
    MenuTitleView = _('&View')
    MenuTitlePerspective = _('Perspectiv&e')
    MenuTitleImport = _('&Import')
    MenuTitleTool = _('&Tool')



# Class Variables
    LoggerName = 'MediaFiler'
    Logger = logging.getLogger(LoggerName)
    LogHandlerInteractive = logging.StreamHandler()  # logging handler to output to visible pane
    LogHandlerFile = None  # logging handler to output to file


## Lifecycle
    def __init__(self,
                 parent,
                 title = '',
                 pos = wx.DefaultPosition,
                 size = wx.Size(1500,600),
                 style = (wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER | wx.CLIP_CHILDREN)):
        # inheritance
        wx.Frame.__init__(self, parent, -1, title, pos, size, style) 
        # internal state
        self.model = None
        self.perspectives = []
        self.presentationActive = False
        self.presentationTimer = None
        # initialize AuiManager managing this frame        
        self.paneManager = wx.aui.AuiManager() 
        self.paneManager.SetManagedWindow(self)
        # create UI components
        # - filter pane, can be hidden, initially hidden
        self.showFilterPane = False     
        self.applyFilter = False
        self.filterPane = MediaFilterPane(self)
        self.paneManager.AddPane(self.filterPane,
                          wx.aui.AuiPaneInfo().Name('filter').Caption(self.PaneCaptionFilter).Left().Layer(3).CloseButton(True).Show(self.showFilterPane))
        # - image tree, can be hidden, initially visible
        self.showTreePane = True
        self.imageTree = MediaTreeCtrl(self, pos=wx.Point(0, 0), size=wx.Size(160, 250))
        self.paneManager.AddPane(self.imageTree,
                          wx.aui.AuiPaneInfo().Name('tree').Caption(self.PaneCaptionImages).Left().Layer(2).CloseButton(True).Show(self.showTreePane))
        # - canvas, cannot be hidden
        self.canvas = MediaCanvas(self);
        self.paneManager.AddPane(self.canvas,
                          wx.aui.AuiPaneInfo().Name('canvas').CenterPane().MaximizeButton(True))
        # - classification pane, initially visible
        self.showClassificationPane = True
        self.classificationPane = MediaClassificationPane(self)
        self.paneManager.AddPane(self.classificationPane,
                          wx.aui.AuiPaneInfo().Name('classification').Caption(self.PaneCaptionClassification).Left().Layer(1).CloseButton(True).Show(self.showClassificationPane))
        # - name pane
        self.namePane = MediaNamePane(self)
        self.paneManager.AddPane (self.namePane,
                           wx.aui.AuiPaneInfo().Name('name').Caption(self.PaneCaptionName).Top().Layer(2).Show(True))
        # - presentation control pane
        self.presentationPane = PresentationControlPane(self)
        self.paneManager.AddPane(self.presentationPane, 
                          wx.aui.AuiPaneInfo().Name('present').BestSize([0,20]).CenterPane().Bottom().Hide())
#         # - log pane, initially hidden
#         self.showLogPane = False
#         self.paneManager.AddPane (self.createLogPane(),
#                            wx.aui.AuiPaneInfo().Name('log').Caption(self.__class__.PaneCaptionLog).Bottom().Layer(4).CloseButton(True).MaximizeButton(True).Show(self.showLogPane))
        # - menu bar must be created after adding panes, to ensure panes exist when creating perspectives
        self.createMenuBar ()
        self.createStatusBar ()
        #  bind events to handler functions
        self.bindEvents() 
        # "commit" all changes made to FrameManager   
        self.paneManager.Update()


    def populateFileMenu (self, menu):
        """Populate the file menu with recently used image directories
        """
        # TODO: replace fixed entries by dynamic history
        index = GUIId.LoadRecentDirectory;
        self.recentRootDirectories = ['N:\\shared\\images\\images', 
                                      'Y:\\home\\Lars\\LarsBilder\\images', 
                                      'Y:\\home\\Paul\\PaulsBilder\\images', 
                                      'Y:\\home\\Gilla\\GillasBilder\\images']
        for name in self.recentRootDirectories:
            menu.Append (index, name)
            index = (index + 1)


    def populatePerspectivesMenu(self, menu):  # @UnusedVariable
        """Populate the perspectives menu.
        """
        self.perspectives = [None for i in range(GUIId.MaxNumberPerspectives)]  # @UnusedVariable
        # save current perspective
        self.perspectives[GUIId.MaxNumberPerspectives - 1] = self.paneManager.SavePerspective()
        # perspective "Classify" to change classification of media
        self.paneManager.GetPane('filter').Hide()
        self.paneManager.GetPane('tree').Show().Left().BestSize(wx.Size(1000,1))
        self.paneManager.GetPane('classification').Show().Left()
        self.paneManager.GetPane('canvas').Show().Center()
        self.paneManager.GetPane('name').Show().Top()
        self.paneManager.GetPane('present').Hide()
        self.paneManager.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexClassify] = self.paneManager.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexClassify), 
                                      self.PerspectiveNameClassify)
        # perspective "Filter" to filter media
        self.paneManager.GetPane('filter').Show().Left()
        self.paneManager.GetPane('tree').Show().Left().BestSize(wx.Size(600,1))
        self.paneManager.GetPane('classification').Hide()
        self.paneManager.GetPane('canvas').Show().Center()
        self.paneManager.GetPane('name').Show().Top()
        self.paneManager.GetPane('present').Hide()
        self.paneManager.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexFilter] = self.paneManager.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexFilter), 
                                      self.PerspectiveNameFilter)
        # perspective "Present" to present media
        self.paneManager.GetPane('filter').Hide()
        self.paneManager.GetPane('tree').Hide()
        self.paneManager.GetPane('classification').Hide()
        self.paneManager.GetPane('canvas').Show().Center()
        self.paneManager.GetPane('name').Hide()
        self.paneManager.GetPane('present').Show().Bottom()
        self.paneManager.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexPresent] = self.paneManager.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexPresent), 
                                      self.PerspectiveNamePresent)
        # perspective "All" containing all panes
        self.perspectives_menu.AppendSeparator()
        self.paneManager.GetPane('filter').Show().Left()
        self.paneManager.GetPane('tree').Show().Left().BestSize(wx.Size(600,1))
        self.paneManager.GetPane('classification').Show().Left()
        self.paneManager.GetPane('canvas').Show().Center()
        self.paneManager.GetPane('name').Show().Top()
        self.paneManager.GetPane('present').Show().Bottom()
        self.paneManager.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexAll] = self.paneManager.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexAll), 
                                      self.PerspectiveNameAll)
        # last used perspective 
        self.perspectives_menu.AppendSeparator()
        self.perspectives_menu.Append((GUIId.LoadPerspective + GUIId.MaxNumberPerspectives - 1),
                                      self.PerspectiveNameLastUsed)
        #menu.Append(GUIId.CreatePerspective, 'Create Perspective')
        # TODO: if perspective loaded, add "Remove this perspective" entry
        self.paneManager.Update()


    def createStatusBar (self):
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-3, -4])


    def createMenuBar (self):
        mb = wx.MenuBar()
        self.SetMenuBar(mb)
        self.menuItemsByName = []
        # File
        file_menu = wx.Menu()
        mb.Append(file_menu, self.MenuTitleFile)
        self.populateFileMenu(file_menu)
        file_menu.Append(GUIId.ChangeRootDirectory, GUIId.FunctionNames[GUIId.ChangeRootDirectory])
        file_menu.AppendSeparator ();
        file_menu.Append(GUIId.ReloadDirectory, GUIId.FunctionNames[GUIId.ReloadDirectory])
        file_menu.Append(GUIId.ExportImages, GUIId.FunctionNames[GUIId.ExportImages])
        file_menu.AppendSeparator ();
        file_menu.Append(wx.ID_EXIT, GUIId.FunctionNames[wx.ID_EXIT])
        # Image
        self.imageMenu = wx.Menu()
        mb.Append(self.imageMenu, self.MenuTitleImage)
        self.imageMenu.Append(GUIId.DeleteImage, GUIId.FunctionNames[GUIId.DeleteImage])
        menuItem = wx.MenuItem(self.imageMenu, GUIId.RandomName, GUIId.FunctionNames[GUIId.RandomName])
        self.menuItemsByName.append(menuItem)
        self.imageMenu.AppendItem(menuItem)
        menuItem = wx.MenuItem(self.imageMenu, GUIId.ChooseName, GUIId.FunctionNames[GUIId.ChooseName])
        self.menuItemsByName.append(menuItem)
        self.imageMenu.AppendItem(menuItem)
        self.imageMenu.Append(GUIId.StartExternalViewer, GUIId.FunctionNames[GUIId.StartExternalViewer])
        self.imageMenu.AppendSeparator()
        self.imageMenu.Append(GUIId.FilterIdentical, GUIId.FunctionNames[GUIId.FilterIdentical])
        self.imageMenu.Append(GUIId.FilterSimilar, GUIId.FunctionNames[GUIId.FilterSimilar])
        # View
        view_menu = wx.Menu ()
        mb.Append (view_menu, self.MenuTitleView)
        view_menu.AppendCheckItem (GUIId.ToggleFilterPane, GUIId.FunctionNames[GUIId.ToggleFilterPane])
        view_menu.AppendCheckItem (GUIId.ToggleFilter, GUIId.FunctionNames[GUIId.ToggleFilter])
        view_menu.Append(GUIId.ClearFilter, GUIId.FunctionNames[GUIId.ClearFilter])
        view_menu.AppendSeparator ();
        view_menu.AppendCheckItem (GUIId.ToggleTreePane, GUIId.FunctionNames[GUIId.ToggleTreePane])
        view_menu.AppendCheckItem (GUIId.ToggleClassificationPane, GUIId.FunctionNames[GUIId.ToggleClassificationPane])
# TODO:        view_menu.AppendCheckItem (GUIId.ToggleLogPane, 'Show Log')
        view_menu.AppendSeparator ();
        view_menu.Append (GUIId.PreviousImage, GUIId.FunctionNames[GUIId.PreviousImage])
        view_menu.Append (GUIId.NextImage, GUIId.FunctionNames[GUIId.NextImage])
        view_menu.Append (GUIId.ResumeSlideshow, GUIId.FunctionNames[GUIId.ResumeSlideshow])
        view_menu.Append (GUIId.StopSlideshow, GUIId.FunctionNames[GUIId.StopSlideshow])
        # Perspectives
        self.perspectives_menu = wx.Menu ()  # instance variable to be accessible when perspectives change
        mb.Append (self.perspectives_menu, self.MenuTitlePerspective)
        self.populatePerspectivesMenu (self.perspectives_menu)
        # Import
        import_menu = wx.Menu ()
        mb.Append (import_menu, self.MenuTitleImport)
        import_menu.Append (GUIId.TestImport, GUIId.FunctionNames[GUIId.TestImport])
        import_menu.Append (GUIId.Import, GUIId.FunctionNames[GUIId.Import])
        import_menu.Append (GUIId.RemoveNew, GUIId.FunctionNames[GUIId.RemoveNew])
        # Tools / Generate
        self.toolsMenu = wx.Menu()
        mb.Append(self.toolsMenu, self.MenuTitleTool)
# TODO:        tools_menu.Append (GUIId.GenerateLinkDirectory, GUIId.FunctionNames[GUIId.GenerateLinkDirectory])
# TODO:        tools_menu.Append (GUIId.GenerateThumbnails, GUIId.FunctionNames[GUIId.GenerateThumbnails])
#        tools_menu.AppendSeparator()
        self.toolsMenu.Append(GUIId.RenameElement, GUIId.FunctionNames[GUIId.RenameElement])
        self.toolsMenu.Append(GUIId.EditClasses, GUIId.FunctionNames[GUIId.EditClasses])
        menuItem = wx.MenuItem(self.toolsMenu, GUIId.EditNames, GUIId.FunctionNames[GUIId.EditNames])
        self.menuItemsByName.append(menuItem)
        self.toolsMenu.AppendItem(menuItem)
        self.toolsMenu.AppendSeparator()
        self.toolsMenu.AppendSubMenu(self.getLoggingMenu(), GUIId.FunctionNames[GUIId.ManageLogging])
#        tools_menu.AppendSeparator()
# TODO:        tools_menu.Append(GUIId.HarvestURLs, GUIId.FunctionNames[GUIId.HarvestURLs])
        

    def getLoggingMenu(self):
        """Return a menu of checkbox items for all modules, to control logging
        """        
        result = wx.Menu()
        modules = self.getLoggableModules()
        cnt = 0
        for module in modules:
            result.AppendCheckItem((GUIId.ManageLogging + cnt), module)
            cnt = (cnt + 1)
            if (GUIId.MaxNumberLogging < cnt):
                break
        # TODO: store & retrieve logging state from configuration
        return(result)


    def createLogPane (self):
        # Create the log for import tests
        self.logPane = wx.Panel(self)
        return(self.logPane)
    
    
    def bindEvents (self):
        """Bind events to functions
        """
        # events triggered from menu bar
        # - file menu
        self.Bind(wx.EVT_MENU, self.onChangeRoot, id=GUIId.ChangeRootDirectory)
        self.Bind(wx.EVT_MENU_RANGE, self.onLoadRecent, id=GUIId.LoadRecentDirectory, id2=(GUIId.LoadRecentDirectory + GUIId.MaxNumberRecentFiles - 1))
        self.Bind(wx.EVT_MENU, self.onReload, id=GUIId.ReloadDirectory)
        self.Bind(wx.EVT_MENU, self.onExport, id=GUIId.ExportImages)
        self.Bind(wx.EVT_MENU, self.onExit, id=wx.ID_EXIT)
        # - image menu
        self.Bind(wx.EVT_MENU_RANGE, self.onDelegateToEntry, id=GUIId.EntryFunctionFirst, id2=GUIId.EntryFunctionLast)
        # - view menu
        self.Bind(wx.EVT_MENU, self.onToggleFilterPane, id=GUIId.ToggleFilterPane)
        self.Bind(wx.EVT_MENU, self.onToggleFilter, id=GUIId.ToggleFilter)
        self.Bind(wx.EVT_MENU, self.filterPane.onClear, id=GUIId.ClearFilter)
        self.Bind(wx.EVT_MENU, self.onToggleTreePane, id=GUIId.ToggleTreePane)
        self.Bind(wx.EVT_MENU, self.onToggleClassificationPane, id=GUIId.ToggleClassificationPane)
        self.Bind(wx.EVT_MENU, self.onToggleLogPane, id=GUIId.ToggleLogPane)
        # - perspectives menu
        self.Bind (wx.EVT_MENU, self.onCreatePerspective, id=GUIId.CreatePerspective)
        self.Bind (wx.EVT_MENU_RANGE, self.onRestorePerspective, id=GUIId.LoadPerspective, id2=(GUIId.LoadPerspective + GUIId.MaxNumberPerspectives - 1))
        # - import menu
        self.Bind (wx.EVT_MENU, self.onImport, id=GUIId.TestImport)
        self.Bind (wx.EVT_MENU, self.onImport, id=GUIId.Import)
        self.Bind (wx.EVT_MENU, self.onRemoveNew, id=GUIId.RemoveNew)
        # - tools menu
        self.Bind(wx.EVT_MENU, self.onEditClasses, id=GUIId.EditClasses)
        self.Bind(wx.EVT_MENU, self.onEditNames, id=GUIId.EditNames)
        self.Bind(wx.EVT_MENU, self.onLoggingChanged, id=GUIId.ManageLogging, id2=(GUIId.ManageLogging + GUIId.MaxNumberLogging))
        self.Bind(wx.EVT_MENU, self.onHarvestURLs, id=GUIId.HarvestURLs)
        # general events
        #        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_CLOSE, self.onExit)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        # Closing Panes Event
        #        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
        #        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUI, id=ID_HorizontalGradient)


# Event Handlers - File Menu events 
    def onLoadRecent(self, event):
        """Change root to selected recent root directory.
        """
        indexOfRecent = (event.GetId() - GUIId.LoadRecentDirectory)
        if (indexOfRecent <= len(self.recentRootDirectories)):
            self.setModel(self.recentRootDirectories[indexOfRecent])


    def onChangeRoot(self, event):  # @UnusedVariable
        """Select new root directory and reload images.
        """
        dialog = wx.DirDialog(self, _('Select New Image Directory:'), style = (wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST))
        if (dialog.ShowModal() == wx.ID_OK):  # user selected directory
            self.setModel(dialog.GetPath())
        dialog.Destroy()  # destroy after getting the user input


    def onReload (self, event):  # @UnusedVariable
        """Reload from current root directory.
        """
        self.setModel(self.model.rootDirectory)


    def onExport(self, event):  # @UnusedVariable
        """User wants to export the (filtered) images.
        
        Ask for target directory and re-create directory structure there. 
        """
        dialog = wx.DirDialog(self, _('Select Directory to Export into:'), style = (wx.DD_DEFAULT_STYLE))
        if (dialog.ShowModal() == wx.ID_OK):  # user selected directory
            wx.BeginBusyCursor()
            if (not os.path.isdir(dialog.GetPath())):
                os.makedirs(dialog.GetPath())
            count = 0
            for entry in self.model:
                if ((not entry.isGroup())
                    and (not entry.filteredFlag)):
                    #print('Exporting "%s" to "%s"' % (entry.getPath(), destination))
                    shutil.copy(entry.getPath(), dialog.GetPath())
                    count = (count + 1)
            wx.EndBusyCursor()
            self.displayInfoMessage(_('%d media exported to "%s"') % (count, dialog.GetPath()))
        dialog.Destroy()  # destroy after getting the user input


    def onExit(self, event):  # @UnusedVariable
        """Close window and terminate.
        """
        #print("MediaFiler.App onExit(")
        self.displayInfoMessage(_('Closing...'))
        self.imageTree.ignoreSelectionChanges = True
        self.imageTree.destroy()
        self.paneManager.UnInit()
        del self.paneManager
        self.Destroy()


# - Image menu events
    def onDelegateToEntry(self, event):
        entry = self.model.getSelectedEntry()
        entry.runContextMenuItem(event.GetId(), self)
   
    
# - View Menu events
    def onToggleFilterPane (self, event):
        """Toggle visibility of filter pane.

        EVENT is the event raised by the CheckMenuItem
        """
        self.showFilterPane = (event.IsChecked())  # toggling done by CheckMenuItem
        self.paneManager.GetPane(self.filterPane).Show(self.showFilterPane)
        self.paneManager.Update()


    def onToggleFilter (self, event):  # @UnusedVariable
        """Toggle filtering of images.

        EVENT is the event raised by the CheckMenuItem
        """
        # toggling menu item is done by CheckMenuItem
        wx.BeginBusyCursor()
        self.model.getFilter().setConditions(active=(not self.model.getFilter().active))
        wx.EndBusyCursor()


    def onToggleTreePane (self, event):
        """Toggle visibility of tree pane. 
            EVENT is the event raised by the CheckMenuItem
        """
        self.showTreePane = event.IsChecked()  # toggling is done by CheckMenuItem
        self.paneManager.GetPane(self.imageTree).Show(self.showTreePane) 
        self.paneManager.Update()
        
    
    def onToggleClassificationPane (self, event):
        """Toggle visibility of classification pane. 
            EVENT is the event raised by the CheckMenuItem
        """
        self.showClassificationPane = event.IsChecked()  # toggling is done by CheckMenuItem
        self.paneManager.GetPane(self.classificationPane).Show(self.showClassificationPane) 
        self.paneManager.Update()


    def onToggleLogPane (self, event):
        """Toggle visibility of log pane. 
            EVENT is the event raised by the CheckMenuItem
        """
        self.showLogPane = event.IsChecked()  # toggling is done by CheckMenuItem
        self.paneManager.GetPane(self.logPane).Show(self.showLogPane)
        self.paneManager.Update()


    def onStartSlideShow (self, event):  # @UnusedVariable
        self.presentationPane.presentNext()
    
    
# - Perspectives Menu events
    def onCreatePerspective (self, event):  # @UnusedVariable
        # Store current window state as perspective.
        dlg = wx.TextEntryDialog(self, "Enter a name for the new perspective:", GUIId.AppTitle)
        dlg.SetValue("Perspective %d" % (len(self.perspectives) + 1))  # TODO: check non-existence of new perspective name
        if (dlg.ShowModal() == wx.ID_OK):  # user entered new perspective name
            self.perspectives.append(self.paneManager.SavePerspective())
            self.populatePerspectivesMenu(self.perspectives_menu)


    def onRestorePerspective (self, event):
        """Switch to the perspective selected by the user.
        """
        perspectiveNumber = (event.GetId() - GUIId.LoadPerspective)
        MediaFiler.Logger.debug('MediaFiler.onRestorePerspective(): Loading perspective %s = %s' % (perspectiveNumber, self.perspectives[perspectiveNumber]))
        self.paneManager.LoadPerspective(self.perspectives[perspectiveNumber])
        self.model.setConfiguration(GlobalConfigurationOptions.LastPerspective, str(perspectiveNumber))


    def onDeletePerspective (self, event):
        """Delete the current perspective.
            EVENT is the event raised by the MenuItem
        """
        pass


# - Import Menu events
    def onImportProfiled(self, event):
        fname = ('%s.profile' % __file__)
        cProfile.runctx('self.onImport(event)',
                        globals(),
                        locals(),
                        fname)
        profile = pstats.Stats(fname)
        profile.strip_dirs().sort_stats('cumulative').print_stats()


    def onImport(self, event):
        """Import images. 
           Ask for a directory to scan (recursively), and import all images contained.
           If event.GetId() == GUIId.TestImport, only show generated filenames, don't actually import anything.
        """
        # variables depending on test mode
        if (event.GetId() == GUIId.TestImport):  
            testRun = True
            statusText = _('Testing import from %s')
        else:  
            testRun = False
            statusText = _('Importing from %s')
        # prepare import parameters
        importParameters = ImportParameterObject(self.model)
        importParameters.setTestRun(testRun)
        # ask user for directory
        dialog = ImportDialog(self, self.model, importParameters)
        if (dialog.ShowModal() == wx.ID_OK):
            wx.BeginBusyCursor()
            self.displayInfoMessage(statusText % dialog.getParameterObject().getImportDirectory())
            try:
                log = self.model.importImages(importParameters)
            except WindowsError as exc: 
                if (exc.winerror == 3):
                    dlg = wx.MessageDialog(self, _('No files to import!'), _('Empty Directory'), (wx.OK | wx.ICON_INFORMATION))
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    raise exc
            else:
                try:
                    logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, log, _('Import Report'), style=wx.RESIZE_BORDER)
                except:
                    logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, _('Import log too large to display.\n\nImport has succeeded.'), _('Import Report'), style=wx.RESIZE_BORDER)
                if (not testRun):
                    self.onReload(None)
                # TODO: make dialog resizable
                logDialog.Maximize(True)  # logDialog.SetSize(wx.Size(1000,600))
                logDialog.ShowModal()
                logDialog.Destroy()
                info = (_('%d media imported from "%s"') if (not testRun) else _('%d media would have been imported from "%s"'))
                self.displayInfoMessage(info % (dialog.getParameterObject().getNumberOfImportedFiles(), dialog.getParameterObject().getImportDirectory()))
            wx.EndBusyCursor()
        dialog.Destroy()  # destroy after getting the user input
    

    def onRemoveNew(self, event):  # @UnusedVariable
        """Remove the new indicator from all (non-filtered) media.
        """
        wx.BeginBusyCursor()
        self.model.getRootEntry().removeNewIndicator()
        wx.EndBusyCursor()



# - Tools Menu events 
    def onGenerateSlideShow (self, event):
        pass
    
    
    def onGenerateTumbnails (self, event):
        pass
    
    
    def onRenameClassElement (self, event):  # @UnusedVariable
        """Rename a class element to another name, in the entire collection. 
        Allows to remove an element if renamed to "".
        """
        MediaFiler.Logger.warn('MediaFiler.onRenameClassElement(): NYI!')
        pass
    
    
    def onEditClasses (self, event):
        """Start external editor on class file.
        """
        classFile = Installer.getClassFilePath()
        editorName = self.model.getConfiguration(GlobalConfigurationOptions.TextEditor)
        if (editorName):
            editorName = editorName.replace(GlobalConfigurationOptions.Parameter, classFile)
            commandArgs = shlex.split(editorName)  # editorName.split() does not respect quotes
            logging.debug('App.onEditClasses(): Calling %s' % commandArgs)
            retCode = subprocess.call(commandArgs, shell=False)
            if (retCode <> 0):
                MediaFiler.Logger.warn('MediaFiler.onEditClasses(): Call failed with return code %s!' % retCode)
                dlg = wx.MessageDialog(self, 
                                       (_('The external program failed with return code %s.') % retCode),
                                       _('Warning'),
                                       wx.OK | wx.ICON_WARNING
                                       )
                dlg.ShowModal()
                dlg.Destroy()
            self.onReload(event)
        else:
            MediaFiler.Logger.warn(_('No editor defined with "%s" configuration option!') % GlobalConfigurationOptions.TextEditor)
            # TODO: error message, but on which window?


    def onEditNames(self, event):  # @UnusedVariable
        """When image collection is organized by names, start external editor on names list.
        """
        if (not self.model.organizedByDate):
            namesFile = Installer.getNamesFilePath()
            editorName = self.model.getConfiguration(GlobalConfigurationOptions.TextEditor)
            if (editorName):
                editorName = editorName.replace(GlobalConfigurationOptions.Parameter, namesFile)
                commandArgs = shlex.split(editorName)
                MediaFiler.Logger.debug('MediaFiler.onEditNames(): Calling %s' % commandArgs)
                retCode = subprocess.call(commandArgs, shell=False)
                if (retCode <> 0):
                    MediaFiler.Logger.warn('App.onEditNames(): Call failed with return code %s!' % retCode)
                    dlg = wx.MessageDialog(self, 
                                           (_('The external program failed with return code %s.') % retCode),
                                           _('Warning'),
                                           wx.OK | wx.ICON_WARNING
                                           )
                    dlg.ShowModal()
                    dlg.Destroy()
            else:
                MediaFiler.Logger.warn(_('App.onEditNames(): No editor defined with "%s" configuration option!') % GlobalConfigurationOptions.TextEditor)
                dlg = wx.MessageDialog(self, 
                                       (_('Define a text editor using configuration option "%s".') % GlobalConfigurationOptions.TextEditor),
                                       _('Warning'),
                                       wx.OK | wx.ICON_WARNING
                                       )
                dlg.ShowModal()
                dlg.Destroy()
        else:
            MediaFiler.Logger.error('App.onEditNames(): MediaFiler.onEditNames(): Only supported when organized by name!')
    

    def onLoggingChanged(self, event):
        """User toggled logging for some module. 
        """
        menu = event.GetEventObject()
        menuId = event.GetId()
        state = menu.IsChecked(menuId)
        loggableModules = self.getLoggableModules()
        moduleName = loggableModules[(menuId - GUIId.ManageLogging)]
        MediaFiler.Logger.debug('MediaFiler.onLoggingChanged(): Turning logging %s for %s' % (('On' if state else 'Off'), moduleName))
        if (state):
            logging.getLogger(moduleName).addHandler(self.__class__.LogHandlerInteractive)
            logging.getLogger(moduleName).debug('User turned on logging for %s' % moduleName)
        else:
            logging.getLogger(moduleName).debug('User turned off logging for %s' % moduleName)
            logging.getLogger(moduleName).removeHandler(self.__class__.LogHandlerInteractive)
        loggedModules = [name for name in loggableModules if menu.IsChecked(menu.FindItem(name))]
        self.model.setConfiguration(GlobalConfigurationOptions.LastLoggedModules,
                                    ' '.join(loggedModules))
    


    def onHarvestURLs(self, event):  # @UnusedVariable
        """When image collection is organized by name, ask for URL to harvest images.
        """
#         if (not self.model.organizedByDate):
#             dialog = URLHarvester.InputDialog.InputDialog(self, -1, self.model)
#             dialog.setSourceURL('')
#             dialog.setLevels(2)
#             if (dialog.ShowModal() == wx.ID_OK):
#                 dialog.execute()
        pass


# - Window Events
    def onResize (self, event):  # @UnusedVariable
        self.GetSizer().Layout()


    def onKeyDown(self, event):
        """User pressed a key.
        
        If PageDown, show next image. 
        If PageUp, show previous image. 
        If Space, resume automatic presentation.
        """
        keyCode = event.GetKeyCode()
        MediaFiler.Logger.debug('MediaFiler.onKeyDown(): Registered "down" for key code %s' % keyCode)
        if (keyCode == 367):  # PageUp 
            self.model.setSelectedEntry(self.model.getSelectedEntry().getNextEntry())
        elif (keyCode == 366):  # PageDown
            self.model.setSelectedEntry(self.model.getSelectedEntry().getPreviousEntry())
        elif (keyCode == 32):  # Space
            self.presentationActive = (not self.presentationActive)
            if (self.presentationActive):
                MediaFiler.Logger.debug('MediaFiler.onKeyDown(): Resume presentation')
                self.presentNext()
            else:
                MediaFiler.Logger.debug('MediaFiler.onKeyDown(): Stop presentation %s' % self.presentationTimer)
                self.presentationTimer.cancel()
            


# Inheritance - ObserverPattern.Observer
    def updateAspect(self, observable, aspect):
        '''ASPECT of OBSERVABLE has changed.
        '''
        if (aspect == 'startFiltering'):  # filter has changed, starting to filter entries
            self.displayInfoMessage('Filtering...')
        elif (aspect == 'stopFiltering'):  # filter has changed, filtering complete
            self.imageTree.DeleteAllItems() 
            self.imageTree.addSubTree(self.model.getRootEntry(), None)
            self.displayInfoMessage('Ok')
        elif (aspect == 'size'):
            self.statusbar.SetStatusText(self.model.getDescription(), GUIId.SB_Organization)
            self.statusbar.Show()
        else:
            MediaFiler.Logger.debug('MediaFiler.updateAspect(): Unhandled change of aspect %s in observable %s' % (aspect, observable))



# Other API Functions
    def displayInfoMessage(self, aString):
        """Display aString in the main window's status bar. 
        """
        self.statusbar.SetStatusText(aString, GUIId.SB_Info)
        self.statusbar.Show()



# section: Internal State
    def setModel(self, directory, progressFunction):
        """Set the model from its root directory.

        Update status and load initial image.
        
        String directory
        Callable progressFunction to show progress
        """
        wx.BeginBusyCursor()
        self.statusbar.SetStatusText(directory, GUIId.SB_Organization)
        self.displayInfoMessage(_('Loading...'))
        MediaFiler.Logger.debug('MediaFiler.setModel(): Loading app icon "%s"' % Installer.getLogoPath())
        self.SetIcon(wx.Icon(Installer.getLogoPath(), wx.BITMAP_TYPE_ICO))
        progressFunction(25)
        self.model = MediaCollection(directory, progressFunction)
        progressFunction(85)
        self.model.addObserverForAspect(self, 'startFiltering')
        self.model.addObserverForAspect(self, 'stopFiltering')
        self.model.addObserverForAspect(self, 'size')
        self.updateMenuAccordingToModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up name pane')
        self.namePane.setModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up filter pane')
        self.filterPane.setModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Filter pane best size is %s' % self.filterPane.GetBestSize())
        self.paneManager.GetPane('filter').BestSize(self.filterPane.GetBestSize())
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up classification pane')
        self.classificationPane.setModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up canvas pane')
        self.canvas.setModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up presentation pane')
        self.presentationPane.setModel(self.model)
        progressFunction(90)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up tree pane')
        self.imageTree.setModel(self.model)
        self.statusbar.SetStatusText(self.model.getDescription(), GUIId.SB_Organization)
        self.statusbar.Show()
        progressFunction(95)
        lastPerspective = self.model.getConfiguration(GlobalConfigurationOptions.LastPerspective)
        if (lastPerspective):
            self.paneManager.LoadPerspective(self.perspectives[int(lastPerspective)])
        self.paneManager.Update()
        self.displayInfoMessage(_('Ready'))
        wx.EndBusyCursor()


    def updateMenuAccordingToModel(self, mediaCollection):
        """Hide/disable the menu entries according to the media organization. 
        
        MediaCollection specifies the model
        """
        if (mediaCollection.organizedByDate):
            for menuItem in self.menuItemsByName:
                menuItem.Enable(False)
        else:  # organized by name
            pass
        if (not mediaCollection.getConfiguration(GlobalConfigurationOptions.TextEditor)):
            self.GetMenuBar().Enable(GUIId.EditClasses, enable=False)
            self.GetMenuBar().Enable(GUIId.EditNames, enable=False)


    def getLoggableModules(self):
        """Return a list of all MediaFiler modules, for toggling logging on the UI.
        """
        result = [MediaFiler.LoggerName]  # include app as well
        def findNames(prefix, pathList):
            MediaFiler.Logger.debug('MediaFiler.getLoggableModules(): Looking at %s' % pathList)
            for dummy, moduleName, isPackage in pkgutil.iter_modules(pathList):
                if (moduleName.find('test') <> 0):
                    result.append(prefix + '.' + moduleName)
                    if (isPackage):
                        findNames((prefix + '.' + moduleName),
                                  [os.path.join(pathList[0], moduleName)])
        import Model  # @UnusedImport
        findNames('Model', Model.__path__)
        import UI  # @Reimport @UnusedImport
        findNames('UI', UI.__path__)
        # findNames('', <sourceDirectory>)  does not find the modules
        MediaFiler.Logger.debug('MediaFiler.getLoggableModules(): Returning %s' % result)
        return(result)


    def setLoggedModules(self):
        """
        """
        loggedModules = self.model.getConfiguration(GlobalConfigurationOptions.LastLoggedModules)
        if (loggedModules):
            loggedModules = loggedModules.split(' ')
            if ('' in loggedModules):
                loggedModules.remove('')
            for moduleName in loggedModules:
                MediaFiler.Logger.debug('MediaFiler.setLoggedModules(): Continuing to log "%s"' % moduleName)
                self.toolsMenu.Check(self.toolsMenu.FindItem(moduleName), True)
                logging.getLogger(moduleName).addHandler(MediaFiler.LogHandlerInteractive)




class MediaFilerApp(ProgressSplashApp):
    """
    """
    def OnInit(self):
        """
        """
        fname = Installer.getSplashPath()
        ProgressSplashApp.OnInit(self, fname)
        fname = os.path.join(Installer.InstallationPath, (Installer.LogFilename % 1))
        logFormatter = logging.Formatter(fmt='%(asctime)s| %(message)s', datefmt='%H:%M:%S')
        logHandler = logging.FileHandler(fname, mode='w')
        logHandler.setFormatter(logFormatter)
        logging.getLogger().addHandler(logHandler)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('MediaFiler.__main__(): Temporarily logging to "%s"' % fname)
        self.SetProgress(5)
        frame = MediaFiler(None, title=GUIId.AppTitle)
        self.SetTopWindow(frame)
        self.SetProgress(10)
        if (Installer.ensureInstallationOk(frame)):
            self.SetProgress(15)
            fname = (Installer.getLogFilePath() % 1)
            logging.debug('MediaFiler.__main__(): Now permanently logging to "%s"' % fname)
            logging.getLogger().removeHandler(logHandler)
            logHandler.close()
            logHandler = logging.FileHandler(fname, mode='w')
            logHandler.setFormatter(logFormatter)
            logging.getLogger().addHandler(logHandler)
            self.SetProgress(20)
            frame.setModel(Installer.getMediaPath(), self.SetProgress)
            self.SetProgress(99)
            frame.setLoggedModules()
            MediaFiler.Logger.debug('MediaFiler.__main__(): App started on %s for "%s"' % (time.strftime('%d.%m.%Y'), Installer.getMediaPath()))
            self.SetProgress(101)
            if (frame.model.getConfiguration(GlobalConfigurationOptions.MaximizeOnStart)):
                MediaFiler.Logger.debug('MediaFiler.__main__(): Maximizing window')
                frame.Maximize(True)
        else:
            app.Exit()
        return(True)


# section: Executable script
if __name__ == "__main__":
    app = MediaFilerApp(False)
    app.MainLoop()


# coding: iso-8859-15

'''(c) by nobisoft 2016-
'''


# Imports
## standard
import os 
#import subprocess
import gettext
import shutil
#import shlex
import logging
import time
import pkgutil
## contributed
import wx.aui
import wx.lib.dialogs
## nobi
from nobi.wx.PhasedProgressBar import PhasedProgressBarError, PhasedProgressBar
from nobi.wx.ResizableDialog import ResizableDialog 
from nobi.ObserverPattern import Observable, Observer
from nobi.wx.ProgressSplashApp import ProgressSplashApp
## project
from Model import GlobalConfigurationOptions
from Model import Installer
from Model.MediaCollection import MediaCollection
from Model.Entry import Entry
from Model import Image  # @UnusedImport import even if "unused", otherwise it's never registered with Installer.ProductTrader
from Model import Movie  # @UnusedImport import even if "unused", otherwise it's never registered with Installer.ProductTrader
from Model.MediaMap import MediaMap  
import UI  # to access UI.PackagePath
from UI import GUIId
from UI.Importing import ImportDialog, ImportParameterObject
from UI.MediaFilterPane import MediaFilterPane
from UI.PresentationControlPane import PresentationControlPane
from UI.MediaTreePane import MediaTreeCtrl
from UI.MediaCanvasPane import MediaCanvas
from UI.MediaNamePane import MediaNamePane
from UI.MediaClassificationPane import MediaClassificationPane
from pickle import NONE
from Model.MediaOrganization import MediaOrganization
from Model.MediaOrganization.OrganizationByName import OrganizationByName



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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
def N_(message): return message



print('Compiling MediaFiler...')

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
    PerspectiveNamePresent = _('Show')
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



# Lifecycle
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
        self.filterPane = MediaFilterPane(self, size=wx.Size(310, 0))
        self.paneManager.AddPane(self.filterPane,
                                 wx.aui.AuiPaneInfo().Name('filter').Caption(self.PaneCaptionFilter).Left().Layer(3).CloseButton(True).Show(self.showFilterPane))
        # - image tree, can be hidden, initially visible
        self.showTreePane = True
        self.imageTree = MediaTreeCtrl(self, pos=wx.Point(0, 0), size=wx.Size(350, 0))
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
        self.recentRootDirectories = ['N:\\shared\\images', 
                                      'Y:\\home\\Lars\\LarsBilder', 
                                      'Y:\\home\\Paul\\PaulsBilder', 
                                      'Y:\\home\\Gilla\\GillasBilder']
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
#         self.statusbar = self.CreateStatusBar(3, wx.ST_SIZEGRIP)  
        self.statusbar = self.CreateStatusBar(3, wx.STB_SIZEGRIP)  # Python 3  
        self.statusbar.SetStatusWidths([-2, -1, -3])  # negative means relative sizes
        self.progressbar = PhasedProgressBar(self.statusbar, -1)
        self.resizeProgressBar()


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
        file_menu.Append(GUIId.RemoveDuplicatesElsewhere, GUIId.FunctionNames[GUIId.RemoveDuplicatesElsewhere])
        file_menu.AppendSeparator ();
        file_menu.Append(wx.ID_EXIT, GUIId.FunctionNames[wx.ID_EXIT])
        # Media
        self.imageMenu = wx.Menu()
        mb.Append(self.imageMenu, self.MenuTitleImage)
        self.imageMenu.Append(GUIId.FindDuplicates, GUIId.FunctionNames[GUIId.FindDuplicates])
        self.imageMenu.Append(GUIId.RemoveAllDuplicates, GUIId.FunctionNames[GUIId.RemoveAllDuplicates])
        self.imageMenu.AppendSeparator()
        self.imageMenu.Append(GUIId.DeleteImage, GUIId.FunctionNames[GUIId.DeleteImage])
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
        self.toolsMenu.Append(GUIId.RenameTag, GUIId.FunctionNames[GUIId.RenameTag])
        self.toolsMenu.Append(GUIId.CountTags, GUIId.FunctionNames[GUIId.CountTags])
        self.toolsMenu.Append(GUIId.EditClasses, GUIId.FunctionNames[GUIId.EditClasses])
        menuItem = wx.MenuItem(self.toolsMenu, GUIId.EditNames, GUIId.FunctionNames[GUIId.EditNames])
        self.menuItemsByName.append(menuItem)
#         self.toolsMenu.AppendItem(menuItem)
        self.toolsMenu.Append(menuItem)  # Python 3
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
                MediaFiler.Logger.debug('MediaFiler.getLoggingMenu(): Restricting menu length to %s' % GUIId.MaxNumberLogging)
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
        self.Bind(wx.EVT_MENU, self.onRemoveDuplicatesElsewhere, id=GUIId.RemoveDuplicatesElsewhere)
        self.Bind(wx.EVT_MENU, self.onExit, id=wx.ID_EXIT)
        # - image menu
        self.Bind(wx.EVT_MENU, self.onFindDuplicates, id=GUIId.FindDuplicates)
        self.Bind(wx.EVT_MENU, self.onRemoveAllDuplicates, id=GUIId.RemoveAllDuplicates)
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
        self.Bind(wx.EVT_MENU, self.onRenameTag, id=GUIId.RenameTag)
        self.Bind(wx.EVT_MENU, self.onCountTags, id=GUIId.CountTags)
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


# Setters
# Getters
    def getProgressBar(self):
        return(self.progressbar)



# Event Handlers - File Menu events 
    def onLoadRecent(self, event):
        """Change root to selected recent root directory.
        """
        indexOfRecent = (event.GetId() - GUIId.LoadRecentDirectory)
        if (indexOfRecent <= len(self.recentRootDirectories)):
            wx.GetApp().startProcessIndicator(_('Loading %s') % self.recentRootDirectories[indexOfRecent])
            self.setModel(self.recentRootDirectories[indexOfRecent])
            wx.GetApp().stopProcessIndicator()


    def onChangeRoot(self, event):  # @UnusedVariable
        """Select new root directory and reload images.
        """
        dialog = wx.DirDialog(self, _('Select New Image Directory:'), style = (wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST))
        if (dialog.ShowModal() == wx.ID_OK):  # user selected directory
            wx.GetApp().startProcessIndicator(_('Loading %s') % dialog.GetPath())
            self.setModel(dialog.GetPath())
            wx.GetApp().stopProcessIndicator()
        dialog.Destroy()  # destroy after getting the user input


    def onReload (self, event):  # @UnusedVariable
        """Reload from current root directory.
        """
        wx.GetApp().startProcessIndicator(_('Reloading...'))
        self.setModel(self.model.rootDirectory)
        wx.GetApp().stopProcessIndicator()


    def onExport(self, event):  # @UnusedVariable
        """User wants to export the (filtered) images.
        
        Ask for target directory and re-create directory structure there. 
        """
        dialog = wx.DirDialog(self, _('Select Directory to Export into:'), style = (wx.DD_DEFAULT_STYLE))
        if (dialog.ShowModal() == wx.ID_OK):  # user selected directory
            progressIndicator = wx.GetApp().startProcessIndicator(_('Exporting to %s') % dialog.GetPath())
            if (not os.path.isdir(dialog.GetPath())):
                os.makedirs(dialog.GetPath())
            count = 0
            progressIndicator.beginPhase(self.model.getCollectionSize())
            for entry in self.model:
                progressIndicator.beginStep()
                if ((not entry.isGroup())
                    and (not entry.filteredFlag)):
                    try:
                        shutil.copy(entry.getPath(), dialog.GetPath())
                    except Exception as e:
                        dlg = wx.MessageDialog(self, 
                                               ('%s' % e),
                                               _('An Error Occurred'),
                                               wx.OK | wx.ICON_INFORMATION) #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL
                        dlg.ShowModal()
                        dlg.Destroy()
                        break
                    count = (count + 1)
            wx.GetApp().stopProcessIndicator(_('%d media exported to "%s"') % (count, dialog.GetPath()))
        dialog.Destroy()  # destroy after getting the user input


    def onExit(self, event):  # @UnusedVariable
        """Close window and terminate.
        """
        #print("MediaFiler.App onExit(")
        wx.GetApp().setInfoMessage(_('Closing...'))
        self.imageTree.ignoreSelectionChanges = True
        self.imageTree.destroy()
        self.paneManager.UnInit()
        del self.paneManager
        self.Destroy()


# - Image menu events
    def onFindDuplicates(self, event):
        """Search for duplicates, merge file names, and remove one. 
        """
        wx.GetApp().startProcessIndicator()
        (collisions, participants) = self.model.findDuplicates(wx.GetApp())
        wx.GetApp().stopProcessIndicator()
        return(_('%s media involved in %s collisions') % (collisions, participants))


    def onRemoveAllDuplicates(self, event):
        """Remove duplicates in entire collection.
        """
        mediaMap = MediaMap.getMap(self.model)
        if (mediaMap == None):
            dlg = wx.MessageDialog(self, 
                                   (_('Create duplicate information first by executing the\n"%s" command.') % GUIId.FunctionNames[GUIId.FindDuplicates]),
                                   _('Error'),
                                   wx.OK | wx.ICON_ERROR) #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL
            dlg.ShowModal()
            dlg.Destroy()
            return(_('No duplicates removed'))
        #TODO: next two lines are identical in Group.deleteDoubles() - how to merge? 
        wx.GetApp().setInfoMessage_('Removing duplicates...') 
        deleted = self.getModel().getRootEntry().deleteDoubles(wx.GetApp().getProgressBar())
        return(GUIId.MessageDuplicatesDeleted % deleted)

        
    def onRemoveDuplicatesElsewhere(self, event):  # @UnusedVariable
        """Ask for another directory and remove all images in there which are contained in this media collection
        """
        def listDirectoryRecursively(pathname):
            result = []
            if (os.path.isdir(pathname)):
                for file in os.listdir(pathname):
                    filename = os.path.join(pathname, file)
                    if (os.path.isdir(filename)):
                        result.extend(listDirectoryRecursively(filename))
                    else:
                        result.append(filename)
            else:
                result.append(pathname)
            return(result)
        
        mediaMap = MediaMap.getMap(self.model)
        if (mediaMap == None):
            dlg = wx.MessageDialog(self, 
                                   ('Create duplicate information first by executing the\n"%s" command.' % GUIId.FunctionNames[GUIId.FindDuplicates]),
                                   _('Error'),
                                   wx.OK | wx.ICON_ERROR) #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL
            dlg.ShowModal()
            dlg.Destroy()
            return()
        dialog = wx.DirDialog(self, _('Select directory to remove duplicates from:'), style = (wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST))
        if (dialog.ShowModal() == wx.ID_OK):  # user selected directory
            count = 0
            if (os.path.isdir(dialog.GetPath())):
                dirname = dialog.GetPath()
                filenameList = listDirectoryRecursively(dirname)
                progressIndicator = wx.GetApp().startProcessIndicator()
                progressIndicator.beginPhase(len(filenameList), message=(_('Removing duplicates in %s') % dirname))
                for filename in filenameList:
                    progressIndicator.beginStep()
                    pathname = os.path.join(dirname, filename)
                    duplicate = mediaMap.getDuplicate(pathname)
                    if (duplicate != None):
                        MediaFiler.Logger.debug('Removing duplicate "%s"' % pathname)
                        # os.remove(pathname)
                        count = (count + 1)
                wx.GetApp().stopProcessIndicator(_('%d media removed in "%s"') % (count, dirname))
        dialog.Destroy()  # destroy after getting the user input


    def onDelegateToEntry(self, event):
        wx.GetApp().startProcessIndicator()
        entry = self.model.getSelectedEntry()
        message = entry.runContextMenuItem(event.GetId(), self)
        wx.GetApp().stopProcessIndicator(message)
   
    
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
        wx.GetApp().startProcessIndicator()
        self.model.getFilter().setConditions(active=(not self.model.getFilter().isActive()))
        wx.GetApp().stopProcessIndicator()


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
    def onImport(self, event):
        """Import images. 
           Ask for a directory to scan (recursively), and import all images contained.
           If event.GetId() == GUIId.TestImport, only show generated filenames, don't actually import anything.
        """
        # prepare import parameters
        importParameters = ImportParameterObject(self.model)
        if (event.GetId() == GUIId.TestImport):  
            importParameters.setTestRun(True)
            messageTemplate = _('%d media would have been imported from "%s"')
        else:  
            importParameters.setTestRun(False)
            messageTemplate = _('%d media imported from "%s"')
        # user dialog asking for more parameters
        dialog = ImportDialog(self, self.model, importParameters)
        if (dialog.ShowModal() == wx.ID_OK):
            wx.GetApp().startProcessIndicator()
            with wx.GetApp() as processIndicator:
                importParameters.setProcessIndicator(processIndicator)
                phases = 1  # minimum: test import
                if (importParameters.getCheckForDuplicates()):  # additional phase for duplicate determination
                    phases = (phases + 1)
                if (not importParameters.getTestRun()):  # additional phase for reloading
                    phases = (phases + 1)
                processIndicator.beginPhase(phases) 
                if (importParameters.getCheckForDuplicates()):
                    importParameters.setMediaMap(MediaMap.getMap(self.model, importParameters.getProcessIndicator()))
                try:
                    log = self.model.importImages(importParameters)
                except WindowsError as exc: 
                    if (exc.winerror == 3):
                        dlg = wx.MessageDialog(self, _('No files to import'), _('Empty Directory'), (wx.OK | wx.ICON_INFORMATION))
                        dlg.ShowModal()
                        dlg.Destroy()
                        message = _('No files to import')
                    else:
                        raise exc
                else:
                    try:
                        logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, log, _('Import Report'), style=wx.RESIZE_BORDER)
                    except:
                        logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, _('Import log too large to display.\n\nImport has succeeded.'), _('Import Report'), style=wx.RESIZE_BORDER)
                    if (not importParameters.getTestRun()):
                        self.setModel(self.model.rootDirectory, processIndicator)
#                    logDialog.Maximize(True) 
                    logDialog.SetMinSize(wx.Size(1000,600))  # TODO: make dialog draggable, it lacks title bar
                    logDialog.EnableCloseButton()
                    logDialog.EnableMaximizeButton()
                    logDialog.Show()
#                    logDialog.Destroy()
                    message = (messageTemplate % (dialog.getParameterObject().getNumberOfImportedFiles(), 
                                                  dialog.getParameterObject().getImportDirectory()))
            wx.GetApp().stopProcessIndicator()
            wx.GetApp().setInfoMessage(message)
        dialog.Destroy() 


    def onRemoveNew(self, event):  # @UnusedVariable
        """Remove the new indicator from all (non-filtered) media.
        """
        wx.GetApp().startProcessIndicator()
        self.model.getRootEntry().removeNewIndicator()
        wx.GetApp().stopProcessIndicator()



# - Tools Menu events 
    def onGenerateSlideShow (self, event):
        pass
    
    
    def onGenerateTumbnails (self, event):
        pass
    
    
    def onRenameTag(self, event):  # @UnusedVariable
        """Rename a class element to another name, in the entire collection. 
        Allows to remove an element if renamed to "".
        """
        dlg = ResizableDialog(parent=self, title=_('Replace tag'))
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(4, 4)
        sizer.Add((5, 5), (0, 0), (1, 1))
        sizer.Add((5, 5), (3, 3), (1, 1))
        sizer.Add(wx.StaticText(dlg, -1, _('Original Tag:')),
                  (1, 1),
                  (1, 1),
                  (wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        originalField = wx.TextCtrl(dlg)
        originalField.SetValue(u'Luebeln')
        sizer.Add(originalField, 
                  (1, 2),
                  (1, 1),
                  (wx.EXPAND|wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        sizer.Add(wx.StaticText(dlg, -1, _('Replacement Tag:')),
                  (2, 1),
                  (1, 1),
                  (wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL))
        replacementField = wx.TextCtrl(dlg)
        replacementField.SetValue(u'L�beln')
        sizer.Add(replacementField, 
                  (2, 2), 
                  (1, 1),
                  (wx.EXPAND|wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
        dlgSizer.Add(sizer)
        dlgSizer.Add(wx.StaticLine(dlg, -1, size=(20, 1), style=wx.LI_HORIZONTAL), (wx.GROW|wx.EXPAND))
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(dlg, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn) 
        btn = wx.Button(dlg, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        dlgSizer.Add(btnsizer, (wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL))
        dlg.SetSizerAndFit(dlgSizer)
        dlg.CenterOnParent()
        result = dlg.ShowModal()
        while (result == wx.ID_OK):
            if (originalField.GetValue() == ''):
                message = _('Original tag may not be empty')
            # elif (replacementField.GetValue() == ''):
            #     message = _('Replacement tag may not be empty')
            elif (originalField.GetValue() == replacementField.GetValue()):
                message = _('Original and replacement may not be identical')
            else:
                message = None
            if (message):
                messageText = wx.StaticText(dlg, -1, message)
                sizer.Add(messageText,
                          (3, 0),
                          (1, 2),
                          (wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL))
                dlg.Fit()
                result = dlg.ShowModal()
                sizer.Remove(messageText)
            else: 
                with wx.GetApp() as progressIndicator:
                    if (replacementField.GetValue() == ''):
                        newTag = None
                    else: 
                        newTag = replacementField.GetValue()
                    message = self.model.replaceTagBy(originalField.GetValue(), newTag, progressIndicator)
                if (message): 
                    self.statusbar.SetStatusText(message, GUIId.SB_Info)
                    self.statusbar.Show()
                result = None
        dlg.Destroy()


    def onCountTags(self, event):
        """Count tag occurrences and show in Dialog
        """
        collectionSize = self.model.getCollectionSize()
        tagOccurrences = self.model.getTagOccurrences()
        msg = ''
        classNames = self.model.getClassHandler().getClassNames()
        for className in classNames:
            classOccurrence = 0
            classMsg = ''
            for tag in self.model.getClassHandler().getElementsOfClassByName(className):
                if (tag in tagOccurrences):
                    classOccurrence = (classOccurrence + tagOccurrences[tag])
                    classMsg = (classMsg + '%-20s %d\n' % (tag, tagOccurrences[tag]))
                else:
                    classMsg = (classMsg + ('%-20s unused\n' % tag))
            msg = (msg + ('%-20s %d %1.2f\n' % (className, classOccurrence, (classOccurrence / collectionSize))) + classMsg + '--\n')
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, _('Tag Occurrences'))
        dlg.ShowModal()
        dlg.Destroy()


    def onEditClasses (self, event):
        """Start external editor on class file.
        """
        classFile = Installer.getClassFilePath()
        self.model.runConfiguredProgram(GlobalConfigurationOptions.TextEditor, classFile, self)
        #TODO: reload classes to make changes effective


    def onEditNames(self, event):  # @UnusedVariable
        """When image collection is organized by names, start external editor on names list.
        """
        if (not self.model.organizedByDate):
            namesFile = Installer.getNamesFilePath()
            self.model.runConfiguredProgram(GlobalConfigurationOptions.TextEditor, namesFile, self)
            OrganizationByName.setNameHandler(self)
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
        else:
            logging.getLogger(moduleName).removeHandler(self.__class__.LogHandlerInteractive)
        # loggedModules = [name for name in loggableModules if menu.IsChecked(menu.FindItem(name))]  # might fail due to limitation of menu entries, therefor:
        loggedModules = []
        for name in loggableModules: 
            i = menu.FindItem(name)
            try:
                if (menu.IsChecked(i)):
                    loggedModules.append(name)
            except: 
                pass  # IsChecked() might fail due to limitation of number of menu entries
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
        self.resizeProgressBar()


    def onKeyDown(self, event):
        """User pressed a key.
        
        If PageDown, show next image. 
        If PageUp, show previous image. 
        If Space, resume automatic presentation.
        If Escape, exit.
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
        elif (keyCode == 27):  # Escape
            self.onExit(None)



# Inheritance - ObserverPattern.Observer
    def updateAspect(self, observable, aspect):
        '''ASPECT of OBSERVABLE has changed.
        '''
        if (aspect == 'startFiltering'):  # filter has changed, starting to filter entries
            wx.GetApp().setInfoMessage('Filtering...')
        elif (aspect == 'stopFiltering'):  # filter has changed, filtering complete
            self.imageTree.DeleteAllItems() 
            self.imageTree.addSubTree(self.model.getRootEntry(), None)
            wx.GetApp().setInfoMessage('')
        elif (aspect == 'size'):
            self.statusbar.SetStatusText(self.model.getDescription(), GUIId.SB_Organization)
            self.statusbar.Show()
        else:
            MediaFiler.Logger.debug('MediaFiler.updateAspect(): Unhandled change of aspect %s in observable %s' % (aspect, observable))



# Other API Functions
# section: Internal State
    def setModel(self, directory, processIndicator=None):
        """Set the model from its root directory.

        Update status and load initial image.
        
        String directory
        ProgressIndicator processIndicator
        """
        self.statusbar.SetStatusText(directory, GUIId.SB_Organization)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Loading app icon "%s"' % Installer.getLogoPath())
        self.SetIcon(wx.Icon(Installer.getLogoPath(), wx.BITMAP_TYPE_ICO))
        if (processIndicator == None):
            processIndicator = wx.GetApp()
        processIndicator.beginPhase(2)
        try:
            self.model = MediaCollection(directory, processIndicator) 
        except Exception as e:
            raise BaseException("Could not create MediaCollection model! \n%s" % e)
        processIndicator.beginPhase(6, (_('Setting up window panes')))
        self.model.addObserverForAspect(self, 'startFiltering')
        self.model.addObserverForAspect(self, 'stopFiltering')
        self.model.addObserverForAspect(self, 'size')
        self.updateMenuAccordingToModel(self.model)
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up name pane')
        self.namePane.setModel(self.model)
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up filter pane')
        self.filterPane.setModel(self.model)
        MediaFiler.Logger.debug('MediaFiler.setModel(): Filter pane best size is %s' % self.filterPane.GetBestSize())
        self.paneManager.GetPane('filter').BestSize(self.filterPane.GetBestSize())
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up classification pane')
        self.classificationPane.setModel(self.model)
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up canvas pane')
        self.canvas.setModel(self.model)  # implicit beginStep()
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up presentation pane')
        self.presentationPane.setModel(self.model)
        processIndicator.beginStep()
        MediaFiler.Logger.debug('MediaFiler.setModel(): Setting up tree pane')
        self.imageTree.setModel(self.model)
        self.statusbar.SetStatusText(self.model.getDescription(), GUIId.SB_Organization)
        self.statusbar.Show()
        lastPerspective = self.model.getConfiguration(GlobalConfigurationOptions.LastPerspective)
        if (lastPerspective):
            self.paneManager.LoadPerspective(self.perspectives[int(lastPerspective)])
        self.paneManager.Update()


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
                if (moduleName.find('test') != 0):
                    result.append(prefix + '.' + moduleName)
                    if (isPackage):
                        findNames((prefix + '.' + moduleName),
                                  [os.path.join(pathList[0], moduleName)])
        # findNames('', <sourceDirectory>)  does not find the modules
        import Model  # @UnusedImport
        findNames('Model', Model.__path__)
        import UI  # @Reimport @UnusedImport
        findNames('UI', UI.__path__)
        result.append('nobi.wx.PhasedProgressBar')
        MediaFiler.Logger.debug('MediaFiler.getLoggableModules(): Returning %s' % result)
        return(result)


    def setLoggedModules(self):
        """
        #TODO: Must be called before MediaCollection.__init__() to log it, but for that, configuration options must be accessible independent of mediacollection
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


    def resizeProgressBar(self):
        if (self.progressbar):
            rect = self.statusbar.GetFieldRect(GUIId.SB_Progress)
            self.progressbar.SetPosition((rect.x+2, rect.y+2))
            self.progressbar.SetSize((rect.width-4, rect.height-4))


print('Compiled MediaFiler, compiling MediaFilerApp...')

class MediaFilerApp(ProgressSplashApp):
    """
    """

# Lifecycle
    def OnInit(self):
        """
        """
        print('Creating MediaFilerApp...')
        self.duringOnInit = True
        fname = Installer.getSplashPath()
        ProgressSplashApp.OnInit(self, fname)
        fname = os.path.join(Installer.InstallationPath, (Installer.LogFilename % 1))
        logFormatter = logging.Formatter(fmt='%(asctime)s| %(message)s', datefmt='%H:%M:%S')
        logHandler = logging.FileHandler(fname, mode='w')
        logHandler.setFormatter(logFormatter)
        logging.getLogger().addHandler(logHandler)
        logging.getLogger().setLevel(logging.DEBUG)
        MediaFiler.Logger.debug('MediaFilerApp.OnInit(): Temporarily logging to "%s"' % fname)
        self.frame = MediaFiler(None, title=GUIId.AppTitle)
        self.SetTopWindow(self.frame)
        if (Installer.ensureInstallationOk(self.frame)):
            fname = (Installer.getLogFilePath() % 1)
            MediaFiler.Logger.debug('MediaFilerApp.OnInit(): Now permanently logging to "%s"' % fname)
            logging.getLogger().removeHandler(logHandler)
            logHandler.close()
            logHandler = logging.FileHandler(fname, mode='w')
            logHandler.setFormatter(logFormatter)
            logging.getLogger().addHandler(logHandler)
            self.frame.setModel(Installer.getMediaPath())        
            self.frame.setLoggedModules()  # TODO: move App itself
            MediaFiler.Logger.debug('MediaFilerApp.OnInit(): App started on %s for "%s"' % (time.strftime('%d.%m.%Y'), Installer.getMediaPath()))
            self.finish(_('Ready'))
            if (self.frame.model.getConfiguration(GlobalConfigurationOptions.MaximizeOnStart)):
                MediaFiler.Logger.debug('MediaFilerApp.OnInit(): Maximizing window')
                self.frame.Maximize(True)
            Entry.CurrentViewportSize = self.frame.GetSize()
            MediaFiler.Logger.debug('MediaFilerApp.OnInit(): Max viewport size is %s' % Entry.CurrentViewportSize)
            self.duringOnInit = False
        else:
            self.Exit()
        print('...MediaFilerApp created')
        return(True)


# Setters
    def setInfoMessage(self, aString):
        """Display aString in the main window's status bar. 
        """
        if (self.duringOnInit):
            self.getProgressText().SetLabel(aString)
            self.getProgressText().Show()
        else:  # OnInit() finished
            # TODO: do not fiddle with frame's variables
            self.frame.statusbar.SetStatusText(aString, GUIId.SB_Info)
            self.frame.statusbar.Show()
        wx.GetApp().ProcessPendingEvents()
        # wx.SafeYield()


# Getters
    def getProgressBar(self):
        """
        """
        if (self.duringOnInit):
            return(super(MediaFilerApp, self).getProgressBar())
        else:  # OnInit() finished
            return(self.frame.getProgressBar())


#     def getInfoMessage(self):
#         """Return the last String set with setInfoMessage()
#         """
#         return(self.frame.statusbar.GetStatusText(GUIId.SB_Info))



# Other API 
    def freezeWidgets(self):
        """Freeze widgets and show busy cursor. 
        """
        wx.BeginBusyCursor()
        self.frame.imageTree.Freeze()
        self.frame.canvas.Freeze()
        

    def thawWidgets(self):
        """Thaw widgets and show regular cursor.
        """
        self.frame.imageTree.Thaw()
        self.frame.canvas.Thaw()
        wx.EndBusyCursor()


    def displayInfoMessage(self, aString):
        print('Deprecated use of MediaFilerApp.displayInfoMessage()')
        self.setInfoMessage(aString)

    
    def createProgressBar(self, message=''):
        return(self.startProcessIndicator(message))


    def startProcessIndicator(self, message=''):
        """Begin a long-running process, and return a PhasedProgressBar to indicate that.
        
        Shows the message, freezes the widgets, and displays the busy cursor as well.
        
        String message to be displayed as information
        Return self, as an object understanding .beginStep() and .beginPhase()
        """
        self.freezeWidgets()
        self.setInfoMessage(message)
        self.getProgressBar().restart()
        MediaFiler.Logger.debug('MediaFilerApp.startProcessIndicator(): Created %s with message "%s"' % (self.getProgressBar(), message))
        self.numberOfStepsToGo = 0 
        return(self)
    
    
    def removeProgressBar(self, message=''):
        self.stopProcessIndicator(message)


    def beginPhase(self, numberOfSteps, message=''):
        MediaFiler.Logger.debug('MediaFilerApp.beginPhase(%s, "%s")' % (numberOfSteps, message))
        self.numberOfStepsToGo = numberOfSteps
        self.setInfoMessage(message)
        self.phaseInfoMessage = message
        self.getProgressBar().beginPhase(numberOfSteps)


    def beginStep(self, message=None):
        if (not message):
            message = self.phaseInfoMessage
        self.setInfoMessage('%s (%d)' % (message, self.numberOfStepsToGo))
        self.numberOfStepsToGo = (self.numberOfStepsToGo - 1)
        self.getProgressBar().beginStep()


    def stopProcessIndicator(self, message=''):
        """The long-running process has finished.
        
        To be called once after each call to startProcessIndicator().
        
        Resets the progress bar, shows the messages, thaws the widgets, and displays the regular cursor. 
        
        String message to be displayed as information
        """
        MediaFiler.Logger.debug('MediaFilerApp.stopProcessIndicator(): %s' % self.frame.getProgressBar())
        if ((not isinstance(message, str)) 
            or (message == '')):
            message = _('Ready')
        self.setInfoMessage(message)
        self.getProgressBar().finish()
        self.thawWidgets()



## Context Manager
    def setRaiseException(self, raiseException):
        """Specify whether exceptions raised inside Context Manager shall be re-raised.
        
        Boolean raiseException indicates exceptions shall be re-raised.
        """
        self.raiseException = raiseException


    def __enter__(self):
        """
        """
        self.setRaiseException(True)
        self.startProcessIndicator()
        return(self)


    def __exit__(self, exceptionType, exceptionValue, exceptionTraceback):
        """
        """
        if (exceptionType == PhasedProgressBarError):
            if (self.raiseException):
                return(False)
            else:
                print('MediaFilerApp.__exit__(). Caught %s %s %s' % (exceptionType, exceptionValue, exceptionTraceback))
                self.stopProcessIndicator()
                return(True)
        elif (exceptionType):  # other exceptions are passed on
            return(False)
        else:  # no exception
            self.stopProcessIndicator()



# section: Executable script
print('Compiled MediaFilerApp, starting __main__')
if __name__ == "__main__":
    app = MediaFilerApp(False)
    print('Created MediaFilerApp')
    app.MainLoop()


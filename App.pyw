'''MediaFiler

A Python 2.7 GUI application which lets you organize media (images and videos). 

(c) by nobisoft 2016-
'''


# Imports
## standard
import os 
import subprocess
import gettext
import shutil
#import threading
import cProfile
import pstats
## contributed
#import wx
#import wx.grid
import wx.aui
#import wx.lib.scrolledpanel
import wx.lib.dialogs
## nobi
from nobi.ObserverPattern import Observable, Observer
## project
from Model import Installer
from Model.MediaCollection import imageFilerModel
from Model import Image  # @UnusedImport import even if "unused", otherwise it's never registered with Entry.ProductTrader
from Model import Movie  # @UnusedImport import even if "unused", otherwise it's never registered with Entry.ProductTrader  
import UI  # to access UI.PackagePath
from UI import GUIId
from UI.Importing import ImportDialog, ImportParameterObject
from UI.MediaFilterPane import MediaFilterPane
from UI.PresentationControlPane import PresentationControlPane
from UI.MediaTreePane import MediaTreeCtrl
from UI.MediaCanvasPane import MediaCanvas
from UI.MediaNamePane import MediaNamePane
from UI.MediaClassificationPane import MediaClassificationPane
#from URLHarvester import URLHarvester
#import URLHarvester.InputDialog



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
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



class MediaFiler (wx.Frame, Observer, Observable):   
    """
    """



# Constants
#    AppTitle = 'MediaFiler'  # window title
    PaneCaptionFilter = _('Filter')
    PaneCaptionImages = _('Image')
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
    ConfigurationOptionLastPerspective = 'last-perspective'


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
        self._mgr = wx.aui.AuiManager() 
        self._mgr.SetManagedWindow(self)
        # create UI components
        # - filter pane, can be hidden, initially hidden
        self.showFilterPane = False     
        self.applyFilter = False
        self.filterPane = MediaFilterPane(self)
        self._mgr.AddPane(self.filterPane,
                          wx.aui.AuiPaneInfo().Name('filter').Caption(self.PaneCaptionFilter).BestSize([300,0]).Left().Layer(3).CloseButton(True).Show(self.showFilterPane))
        # - image tree, can be hidden, initially visible
        self.showTreePane = True
        self.imageTree = MediaTreeCtrl(self, pos=wx.Point(0, 0), size=wx.Size(160, 250))
        self._mgr.AddPane(self.imageTree,
                          wx.aui.AuiPaneInfo().Name('tree').Caption(self.PaneCaptionImages).BestSize([400,0]).Left().Layer(2).CloseButton(True).Show(self.showTreePane))
        # - canvas, cannot be hidden
        self.canvas = MediaCanvas(self);
        self._mgr.AddPane(self.canvas,
                          wx.aui.AuiPaneInfo().Name('canvas').CenterPane().MaximizeButton(True))
        # - classification pane, initially visible
        self.showClassificationPane = True
        self.classificationPane = MediaClassificationPane(self)  #ObsoleteImageClassificationPane.ObsoleteImageClassificationPane(self)
        self._mgr.AddPane(self.classificationPane,
                          wx.aui.AuiPaneInfo().Name('classification').Caption(self.PaneCaptionClassification).BestSize((400,0)).Left().Layer(1).CloseButton(True).Show(self.showClassificationPane))
        # - name pane
        self.namePane = MediaNamePane(self)
        self._mgr.AddPane (self.namePane,
                           wx.aui.AuiPaneInfo().Name('name').Caption(self.PaneCaptionName).BestSize ([0,20]).Top().Layer(2).Show(True))
        # - presentation control pane
        self.presentationPane = PresentationControlPane(self)
        self._mgr.AddPane(self.presentationPane, 
                          wx.aui.AuiPaneInfo().Name('present').BestSize([0,20]).CenterPane().Bottom().Hide())
#         # - log pane, initially hidden
#         self.showLogPane = False
#         self._mgr.AddPane (self.createLogPane(),
#                            wx.aui.AuiPaneInfo().Name('log').Caption(self.__class__.PaneCaptionLog).Bottom().Layer(4).CloseButton(True).MaximizeButton(True).Show(self.showLogPane))
        # - menu bar must be created after adding panes, to ensure panes exist when creating perspectives
        self.createMenuBar ()
        self.createStatusBar ()
        #  bind events to handler functions
        self.bindEvents() 
        # "commit" all changes made to FrameManager   
        self._mgr.Update()


    def populateFileMenu (self, menu):
        """Populate the file menu with recently used image directories
        """
        # TODO: replace fixed entries by dynamic history
        index = GUIId.LoadRecentDirectory;
        self.recentRootDirectories = ['N:\\shared\\images\\family', 
                                      'Y:\home\Paul\PaulsBilder\images', 
                                      'Y:\home\Gilla\GillasBilder\images']
        for name in self.recentRootDirectories:
            menu.Append (index, name)
            index = (index + 1)


    def populatePerspectivesMenu(self, menu):  # @UnusedVariable
        """Populate the perspectives menu.
        """
        self.perspectives = [None for i in range(GUIId.MaxNumberPerspectives)]  # @UnusedVariable
        # save current perspective
        self.perspectives[GUIId.MaxNumberPerspectives - 1] = self._mgr.SavePerspective()
        # perspective "Classify" to change classification of media
        self._mgr.GetPane('filter').Hide()
        self._mgr.GetPane('tree').Show().Left()
        self._mgr.GetPane('classification').Show().Left()
        self._mgr.GetPane('canvas').Show().Center()
        self._mgr.GetPane('name').Show().Top()
        self._mgr.GetPane('present').Hide()
        self._mgr.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexClassify] = self._mgr.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexClassify), 
                                      self.PerspectiveNameClassify)
        # perspective "Filter" to filter media
        self._mgr.GetPane('filter').Show().Left()
        self._mgr.GetPane('tree').Show().Left()
        self._mgr.GetPane('classification').Hide()
        self._mgr.GetPane('canvas').Show().Center()
        self._mgr.GetPane('name').Show().Top()
        self._mgr.GetPane('present').Hide()
        self._mgr.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexFilter] = self._mgr.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexFilter), 
                                      self.PerspectiveNameFilter)
        # perspective "Present" to present media
        self._mgr.GetPane('filter').Hide()
        self._mgr.GetPane('tree').Hide()
        self._mgr.GetPane('classification').Hide()
        self._mgr.GetPane('canvas').Show().Center()
        self._mgr.GetPane('name').Hide()
        self._mgr.GetPane('present').Show().Bottom()
        self._mgr.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexPresent] = self._mgr.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexPresent), 
                                      self.PerspectiveNamePresent)
        # perspective "All" containing all panes
        self.perspectives_menu.AppendSeparator()
        self._mgr.GetPane('filter').Show().Left()
        self._mgr.GetPane('tree').Show().Left()
        self._mgr.GetPane('classification').Show().Left()
        self._mgr.GetPane('canvas').Show().Center()
        self._mgr.GetPane('name').Show().Top()
        self._mgr.GetPane('present').Show().Bottom()
        self._mgr.GetPane('log').Hide()
        self.perspectives[self.PerspectiveIndexAll] = self._mgr.SavePerspective()
        self.perspectives_menu.Append((GUIId.LoadPerspective + self.PerspectiveIndexAll), 
                                      self.PerspectiveNameAll)
        # last used perspective 
        self.perspectives_menu.AppendSeparator()
        self.perspectives_menu.Append((GUIId.LoadPerspective + GUIId.MaxNumberPerspectives - 1),
                                      self.PerspectiveNameLastUsed)
        #menu.Append(GUIId.CreatePerspective, 'Create Perspective')
        # TODO: if perspective loaded, add "Remove this perspective" entry
        self._mgr.Update()



    def createStatusBar (self):
        self.statusbar = self.CreateStatusBar(3, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3, -1])


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
        tools_menu = wx.Menu ()
        mb.Append (tools_menu, self.MenuTitleTool)
# TODO:        tools_menu.Append (GUIId.GenerateLinkDirectory, GUIId.FunctionNames[GUIId.GenerateLinkDirectory])
# TODO:        tools_menu.Append (GUIId.GenerateThumbnails, GUIId.FunctionNames[GUIId.GenerateThumbnails])
#        tools_menu.AppendSeparator()
        tools_menu.Append(GUIId.RenameElement, GUIId.FunctionNames[GUIId.RenameElement])
        tools_menu.Append(GUIId.EditClasses, GUIId.FunctionNames[GUIId.EditClasses])        
        if (False):  # TODO: (not self.model.organizedByDate): does not work since model not defined yet
            tools_menu.Append(GUIId.EditNames, GUIId.FunctionNames[GUIId.EditNames])
#        tools_menu.AppendSeparator()
# TODO:        tools_menu.Append(GUIId.HarvestURLs, GUIId.FunctionNames[GUIId.HarvestURLs])
        
        
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
        self.Bind(wx.EVT_MENU, self.onEditClasses, id = GUIId.EditClasses)
        self.Bind(wx.EVT_MENU, self.onEditNames, id=GUIId.EditNames)
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
        self._mgr.UnInit()
        del self._mgr
        self.Destroy()


# - Image menu events
    def onDelegateToEntry(self, event):
        entry = self.model.getSelectedEntry()
        if (entry):
            entry.runContextMenuItem(event.GetId(), self)
   
    
# - View Menu events
    def onToggleFilterPane (self, event):
        """Toggle visibility of filter pane.

        EVENT is the event raised by the CheckMenuItem
        """
        self.showFilterPane = (event.IsChecked())  # toggling done by CheckMenuItem
        self._mgr.GetPane(self.filterPane).Show(self.showFilterPane)
        self._mgr.Update()


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
        self._mgr.GetPane(self.imageTree).Show(self.showTreePane) 
        self._mgr.Update()
        
    
    def onToggleClassificationPane (self, event):
        """Toggle visibility of classification pane. 
            EVENT is the event raised by the CheckMenuItem
        """
        self.showClassificationPane = event.IsChecked()  # toggling is done by CheckMenuItem
        self._mgr.GetPane(self.classificationPane).Show(self.showClassificationPane) 
        self._mgr.Update()


    def onToggleLogPane (self, event):
        """Toggle visibility of log pane. 
            EVENT is the event raised by the CheckMenuItem
        """
        self.showLogPane = event.IsChecked()  # toggling is done by CheckMenuItem
        self._mgr.GetPane(self.logPane).Show(self.showLogPane)
        self._mgr.Update()


    def onStartSlideShow (self, event):  # @UnusedVariable
        self.presentationPane.presentNext()
    
    
# - Perspectives Menu events
    def onCreatePerspective (self, event):  # @UnusedVariable
        # Store current window state as perspective.
        dlg = wx.TextEntryDialog(self, "Enter a name for the new perspective:", GUIId.AppTitle)
        dlg.SetValue("Perspective %d" % (len(self.perspectives) + 1))  # TODO: check non-existence of new name
        if (dlg.ShowModal() == wx.ID_OK):  # user entered new perspective name
            self.perspectives.append(self._mgr.SavePerspective())
            self.populatePerspectivesMenu(self.perspectives_menu)


    def onRestorePerspective (self, event):
        """Switch to the perspective selected by the user.
        """
        perspectiveNumber = (event.GetId() - GUIId.LoadPerspective)
        print('Loading perspective %s = %s' % (perspectiveNumber, self.perspectives[perspectiveNumber]))
        self._mgr.LoadPerspective(self.perspectives[perspectiveNumber])
        self.model.setConfiguration(self.ConfigurationOptionLastPerspective, str(perspectiveNumber))


    def onDeletePerspective (self, event):
        """Delete the current perspective.
            EVENT is the event raised by the MenuItem
        """
        # TODO:
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
        if (event.GetId() == GUIId.TestImport):  # only test
            testRun = True
            statusText = _('Testing import from %s')
        else:  # really import
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
            log = self.model.importImages(importParameters)
            try:
                logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, log, _('Import Report'), style=wx.RESIZE_BORDER)
            except:
                logDialog = wx.lib.dialogs.ScrolledMessageDialog(self, _('Import log too large to display.\n\nImport has succeeded.'), _('Import Report'), style=wx.RESIZE_BORDER)
            # TODO: make dialog resizable
            logDialog.SetSize(wx.Size(1000,600))
            logDialog.Show()
            self.onReload(None)
            self.displayInfoMessage(_('%d media imported from %s') % (dialog.getParameterObject().getNumberOfImportedFiles(), dialog.getParameterObject().getImportDirectory()))
            wx.EndBusyCursor()
        dialog.Destroy()  # destroy after getting the user input
    

    def onRemoveNew(self, event):  # @UnusedVariable
        """Remove the new indicator from all (non-filtered) media.
        """
        wx.BeginBusyCursor()
        self.model.getRootNode().removeNewIndicator()
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
        # TODO:
        print('NYI: Rename Class Element')
        pass
    
    
    def onEditClasses (self, event):
        """Start external editor on class file.
        """
        classFile = Installer.getClassFilePath(os.path.join(self.model.rootDirectory, '..'))  # TODO: fix root directory
#        classFile = os.path.join(self.model.rootDirectory, imageFilerModel.ClassFileName)
        subprocess.call(['C:/Program Files (x86)/Gnu/Emacs-24.5/bin/runemacs.exe', classFile], shell=True)
        # reload current model
        self.onReload(event)
        pass
    
    
    def onEditNames (self, event):  # @UnusedVariable
        """When image collection is organized by names, start external editor on names list.
        """
        if (not self.model.organizedByDate):
            nameFile = self.model.rootDirectory + imageFilerModel.NamesFileName
            subprocess.call(['C:/Program Files (x86)/Gnu/Emacs-24.5/bin/runemacs.exe', nameFile], shell=True)
        else:
            print('Not supported!')
    

    def onHarvestURLs(self, event):  # @UnusedVariable
        """When image collection is organized by name, ask for URL to harvest images.
        """
#         if (not self.model.organizedByDate):
#             dialog = URLHarvester.InputDialog.InputDialog(self, -1, self.model)
#             dialog.setSourceURL('http://nudemodel.pics/errotica-archives/nessa-cigarillo/')
#             dialog.setLevels(2)
#             if (dialog.ShowModal() == wx.ID_OK):
#                 dialog.execute()



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
        print('Registered "down" for key code %s' % keyCode)
        if (keyCode == 367):  # PageUp 
            self.model.setSelectedEntry(self.model.getNextEntry(self.model.getSelectedEntry()))
        elif (keyCode == 366):  # PageDown
            self.model.setSelectedEntry(self.model.getPreviousEntry(self.model.getSelectedEntry()))
        elif (keyCode == 32):  # Space
            self.presentationActive = (not self.presentationActive)
            if (self.presentationActive):
                print('Resume presentation')
                self.presentNext()
            else:
                print('Stop presentation %s' % self.presentationTimer)
                self.presentationTimer.cancel()
            


        
# Inheritance - ObserverPattern.Observer
    def updateAspect(self, observable, aspect):
        '''ASPECT of OBSERVABLE has changed.
        '''
        if (aspect == 'startFiltering'):  # filter has changed, starting to filter entries
            self.displayInfoMessage('Filtering...')
        elif (aspect == 'stopFiltering'):  # filter has changed, filtering complete
            self.imageTree.DeleteAllItems() 
            self.imageTree.addSubTree(self.model.getRootNode(), None)
            self.displayInfoMessage('Ok')
        else:
            print 'Unhandled change of aspect %s in observable %s' % (aspect, observable)
#            pass



# Other API Functions
    def displayInfoMessage(self, aString):
        """Display aString in the main window's status bar. 
        """
        self.statusbar.SetStatusText(aString, GUIId.SB_Info)
        self.statusbar.Show()



# section: Internal State
    def setModel(self, directory):
        """Set the model from its root DIRECTORY. Update status and load initial image.
        """
        wx.BeginBusyCursor()
        directory = unicode(directory)
        # update status bar
        self.statusbar.SetStatusText(directory, GUIId.SB_Root)
        self.displayInfoMessage(_('Loading...'))
        # set window icon
        print('Setting app icon from "%s"' % os.path.join(directory, '../lib/logo.ico'))
        self.SetIcon(wx.Icon(os.path.join(directory, '../lib/logo.ico'), wx.BITMAP_TYPE_ICO))
        # create the model
        self.model = imageFilerModel(directory)
        self.model.addObserverForAspect(self, 'startFiltering')
        self.model.addObserverForAspect(self, 'stopFiltering')
        # update status bar
        if (self.model.organizedByDate):
            self.statusbar.SetStatusText (_('Organized by date'), GUIId.SB_Organization)
        else:
            text = _('%s (%d used, %d free)') % (directory, len(self.model.names), len(self.model.freeNames)) 
            self.statusbar.SetStatusText(text, GUIId.SB_Root)           
            self.statusbar.SetStatusText(_('Organized by name'), GUIId.SB_Organization)
        self.statusbar.Show()
        # update UI
        self.updateMenuAccordingToOrganization(self.model.organizedByDate)
        self.namePane.setModel(self.model)
        self.filterPane.setModel(self.model)
        self.classificationPane.setModel(self.model)
        self.canvas.setModel(self.model)
        self.presentationPane.setModel(self.model)
        self.imageTree.setModel(self.model)
        # load last viewed perspective
        lastPerspective = self.model.getConfiguration(self.ConfigurationOptionLastPerspective)
        if (lastPerspective):
            self._mgr.LoadPerspective(self.perspectives[int(lastPerspective)])
        # update status bar
        self.displayInfoMessage(_('Ready.'))
        wx.EndBusyCursor()


    def updateMenuAccordingToOrganization(self, organizationByDate):
        """Hide/show the menu entries according to the media organization. 
        
        Boolean organizationByDate indicates that media is organized by date
        """
        for menuItem in self.menuItemsByName:
            menuItem.Enable(not organizationByDate)



# Functions
def prepareFilesAndFolders(frame, path):
    """Ask user for the directory to create the media directory in, and prepare it.
    
    wx.Frame frame contains parent window for Dialog
    String path contains a default path
    Return String containing media root folder
        or None
    """
    result = None
    dlg = wx.DirDialog(frame, "The current working directory for this program is not a valid media directory. Choose a media directory:", style=wx.DD_DEFAULT_STYLE)
    dlg.SetPath(path)
    if (dlg.ShowModal() == wx.ID_OK):
        newPath = dlg.GetPath()
        if (os.path.isdir(newPath) 
            and Installer.checkInstallation(newPath)):
            result = newPath
        else:
            Installer.install(newPath)
            result = newPath
    dlg.Destroy()
    return(result)


# section: Executable script
if __name__ == "__main__":
    app = wx.App(False)    
    frame = MediaFiler(None, title=GUIId.AppTitle)
    frame.Show()
    (path, dummy) = os.path.split(os.getcwd())
    if (dummy == ''):
        (path, dummy) = os.path.split(path)
    if (not Installer.checkInstallation(path)):
        path = prepareFilesAndFolders(frame, path)
    if (path):
        frame.setModel(Installer.getImagePath(path))  # TODO: correct root folder
        app.MainLoop()
    

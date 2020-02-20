# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""

# Imports
## standard
import gettext
import os.path
import logging
## contributed
import wx
## nobi
from nobi.ObserverPattern import Observer, Observable
#from nobi.PausableObservable import PausableObservable
## project
import UI
from UI import GUIId
#import Model.Image 
import Model.Installer



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
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
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class MediaTreeCtrl (wx.TreeCtrl, Observable, Observer):
    """The MediaTreeCtrl displays a hierarchy of all media in its model, an ImageFilerModel.

    ObserverPattern aspects:
    selection: the selection changed
    """



# Constants
#     Logger = logging.getLogger(__name__)



# section: Lifecycle
    def __init__ (self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TR_DEFAULT_STYLE):
        # initialize superclasses
        wx.TreeCtrl.__init__(self, parent, pos=pos, size=size, style=(style | wx.NO_BORDER | wx.TR_HIDE_ROOT | wx.TR_TWIST_BUTTONS ))  # | wx.TR_MULTIPLE)) 
        Observer.__init__(self)
        Observable.__init__(self, ['selection'])
        # define norgy images
        imglist = wx.ImageList(16, 16, True, 3)
        self.closedFolderIcon = imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, wx.Size(16, 16)))
        self.openFolderIcon = imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, wx.Size(16, 16)))
        self.fallBackTypeIconIndex = imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size(16, 16)))
        self.AssignImageList(imglist)
        # bind events triggered by tree
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelectionChanged, self)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.onContextMenuRequest, self)
        self.Bind(wx.EVT_MENU_RANGE, self.onContextMenuSelection, id=GUIId.EntryFunctionFirst, id2=GUIId.EntryFunctionLast)  # context menu actions on Entry objects
        #self.Bind(wx.EVT_SIZE, self.onResize)  # called too often
        # internal state
        self.model = None  
        self.selectionBeforeFiltering = None  # selected Entry before filtering started, to detect whether it is filtered
        self.ignoreSelectionChanges = False  # flag to stop onSelectionChanged events when mass deleting
        self.oldSize = self.Size



# Setters
    def setModel(self, model):
        """Set imageFilerModel
        """
        if (self.model):
            self.DeleteAllItems()
            self.model.removeObserver(self)
        self.model = model
        self.model.addObserverForAspect(self, 'selection')
        self.model.addObserverForAspect(self, 'startFiltering')
        self.model.addObserverForAspect(self, 'stopFiltering')
        # 
        self.typeIconsIndices = {}
        for c in Model.Installer.getProductTrader().getClasses():
            pathname = os.path.join(Model.Installer.getLibraryPath(), (c.__name__ + '.jpg'))
            try:
                icon = wx.Image(os.path.join(Model.Installer.getLibraryPath(), pathname), 
                                wx.BITMAP_TYPE_JPEG).Rescale(16, 16).ConvertToBitmap()
                index = self.GetImageList().Add(icon)
                self.typeIconsIndices[c] = index
            except Exception as e:
                Logger.warning('MediaTreeCtrl.setModel(): Cannot find type icon for class "%s"' % c)
                self.typeIconsIndices[c] = self.fallBackTypeIconIndex
        #
        self.addSubTree(self.model.getRootEntry(), None)
        self.setEntry(self.model.getSelectedEntry())


    def addSubTree(self, entry, parent):
        """Add a tree node for imageFilerEntry ENTRY under wx.TreeItemID PARENT, and recurse to add all descendants.

        Entry entry is the MediaFiler.Entry to add
        wx.TreeItemID parent the node of the subtree to add. If parent is None, entry is the root node. 

        Return the wx.TreeItemID of entry.
        """
        if (entry.filteredFlag):
            print('MediaTreeCtrl.addSubTree(): Ignoring filtered Entry "%s"' % entry.getPath())
            return(None)
        # create a tree item
        item = wx.TreeItemData(entry)
        # insert tree item
        if (entry.isGroup()):  # entry is a Group, add a collapsible node for entry
            if (parent == None):  # entry is root Group
                node = self.AddRoot("All", 
                                    self.closedFolderIcon, 
                                    self.openFolderIcon, 
                                    data=item)  
            else:   
                node = self.AppendItem(parent, 
                                       entry.getFilename(), 
                                       self.closedFolderIcon, 
                                       self.openFolderIcon, 
                                       data=item)
            for subentry in entry.getSubEntries():
                if (not subentry.filteredFlag):
                    self.addSubTree(subentry, node)
        else:  # add a leaf for entry
            node = self.AppendItem(parent, 
                                   entry.getFilename(), 
                                   self.typeIconsIndices[entry.__class__], 
                                   data=item)
            if (not node):  # should not happen, report
                print('MediaTreePane.addSubTree(): AppendItem returned None for (%s, %s, %s, %s)' 
                      % (parent, entry.getFilename(), self.typeIconsIndices[entry.__class__], item))
        # register as observer for entry
        entry.addObserverForAspect(self, 'name')
        entry.addObserverForAspect(self, 'remove')
        entry.addObserverForAspect(self, 'children')
        # store wx.TreeItemID in entry for reverse lookup
        entry.setTreeItemID(node)
        self.SortChildren(node)
        return(node)


    def setEntry(self, entry, expand=False):
        """Select the specified entry in the tree.
        
        Boolean expand indicates that the selected node shall be expanded.
        """
        Logger.debug('MediaTreeCtrl.setEntry(%s)' % entry)
        self.Freeze()
        if (entry.getTreeItemID()):
            self.SelectItem(entry.getTreeItemID())
            if (expand):
                self.Expand(entry.getTreeItemID())
            self.EnsureVisible(entry.getTreeItemID())
# safety only
#             if (self.GetItemData(entry.getTreeItemID())):
#                 if (entry <> self.GetItemData(entry.getTreeItemID()).GetData()):
#                     Logger.error('MediaTreeCtrl.setEntry(): Inconsistent data (%sfiltered) for %s' % (('un' if entry.isFiltered() else ''), entry))     
#             else: 
#                 Logger.error('MediaTreeCtrl.setEntry(): No item data for tree item "%s"' % entry)
        else:
            Logger.error('MediaTreeCtrl.setEntry(): No tree item ID for "%s"' % entry)
        self.Thaw()


# Getters
# Event Handlers
    def onSelectionChanged (self, event):
        """User changed the selection in the tree.
        """
        if (self.ignoreSelectionChanges): 
            pass
        else:
            entry = self.GetItemData(event.GetItem()).GetData()
            Logger.debug('MediaTreeCtrl.onSelectionChanged(): Selecting "%s"' % entry)
            self.ignoreSelectionChanges = True
            wx.GetApp().startProcessIndicator()
            self.model.setSelectedEntry(entry)
            wx.GetApp().stopProcessIndicator()
            self.ignoreSelectionChanges = False


    def onContextMenuRequest (self, event):
        """User pressed context menu button in the tree.
        """
        entry = self.GetItemData(event.GetItem()).GetData()
        menu = entry.getContextMenu()  # create context menu for current Entry
        self.PopupMenu(menu)  # let user select item
        menu.Destroy()


    def onContextMenuSelection(self, event):
        """User selected an item in a context menu. 
        
        Route to selected Entry.
        """
        Logger.debug('MediaTreePane.onContextMenuSelection(): User selected item %s' % event.Id)
        wx.GetApp().startProcessIndicator()
        message = event.EventObject.currentEntry.runContextMenuItem(event.Id, self)
        wx.GetApp().stopProcessIndicator(message)


    def onResize(self, event): 
        """After conventional resizing, ensure selected entry is still visible.
        """
        if (self.oldSize <> event.GetSize()):
            Logger.debug('MediaTreeCtrl.onResize: Resizing from %s to %s' % (self.oldSize, event.GetSize()))
        self.oldSize = event.GetSize()
        if (self.model
            and self.model.getSelectedEntry().getTreeItemID()
            and (not self.IsVisible(self.model.getSelectedEntry().getTreeItemID()))):
            wx.CallAfter(self.EnsureVisible, self.model.getSelectedEntry().getTreeItemID())
            Logger.debug('MediaTreeCtrl.onResize: Queued "EnsureVisible(%s)"' % self.model.getSelectedEntry().getPath())
        event.Skip()


    
# Inheritance - Observer
    def updateAspect(self, observable, aspect):
        """ASPECT of OBSERVABLE changed. 
        """
        self.Freeze()
        if (aspect == 'name'):  # name of an Entry changed
            node = observable.getTreeItemID()
            self.SetItemText(node, observable.getFilename())
            self.SortChildren(self.GetItemParent(node))
            self.EnsureVisible(node)
            Logger.debug('MediaTreeCtrl.updateAspect(): Changed name of %s' % observable)
        elif (aspect == 'remove'):  # Entry deleted
            observable.removeObserver(self)
            node = observable.getTreeItemID()
            self.Delete(node)
            Logger.debug('MediaTreeCtrl.update(): Removed %s' % observable)
        elif (aspect == 'children'):  # Group changes its children
            node = observable.getTreeItemID()
            self.ignoreSelectionChanges = True
            self.DeleteChildren(node)
            for subEntry in observable.getSubEntries():
                self.addSubTree(subEntry, node)
            self.SortChildren(node)
            self.ignoreSelectionChanges = False
            self.setEntry(self.model.getSelectedEntry())
            Logger.debug('MediaTreeCtrl.updateAspect(): Changed children of %s' % observable.getPath())
        elif (aspect == 'selection'):  # model changed selection
            entry = observable.getSelectedEntry()
            self.ignoreSelectionChanges = True
            self.setEntry(entry)
            self.ignoreSelectionChanges = False
            Logger.debug('MediaTreeCtrl.updateAspect(): Selected %s' % entry)
        elif (aspect == 'startFiltering'):  # filter changed, remember current selection
            self.selectionBeforeFiltering = self.model.getSelectedEntry()
            self.storeExpansionState()
            Logger.debug('MediaTreeCtrl.updateAspect(): Stored state before filtering')
        elif (aspect == 'stopFiltering'):  # filtering done, try to restore selection
            self.Freeze()
            self.DeleteAllItems()
            self.addSubTree(self.model.getRootEntry(), None)
            if (self.selectionBeforeFiltering <> self.model.getSelectedEntry()):
                self.setEntry(self.model.getSelectedEntry(), expand=True)
            else:
                self.setEntry(self.model.getSelectedEntry())
            self.restoreExpansionState()
            self.Thaw()
            Logger.debug('MediaTreeCtrl.updateAspect(): Recreated tree state after filtering')
        else:
            super(MediaTreeCtrl, self).update(observable, aspect)
        self.Thaw()


# Inheritance - wx.TreeCtrl
    def EnsureVisible(self, *args, **kwargs):
        """Ensure that the tree item passed in args[0] is visible on screen. 
        
        This is a mess: 
        self.IsVisible(item) nearly always returns False, irrespective of display
        self.GetBoundingRect(item) returns (x, y, w, h) 
        self.GetClientSize() returns (1, 1)
        self.GetClientRect() returns (0, 0, 1, 1)
        self.GetSize() returns (1, 1)
        self.GetPrevVisible(item) requires item to be visible, which cannot be ensured if IsVisible() and EnsureVisible() don't work.
        self.ScrollTo(item) scrolls item just out of view above viewport.
        
        As long as GetClientSize() does not return the correct height, it can't be determined 
        whether the item is visible or scrolled out of the bottom.
        
        """
        if (isinstance(self, MediaTreeCtrl)):
            item = args[0]
            if (self.GetItemData(item)):
                entry = self.GetItemData(item).GetData()
                Logger.debug('MediaTreeCtrl.EnsureVisible(%s)' % entry)
                Logger.debug('MediaTreeCtrl.EnsureVisible(): IsVisible()=%s' % self.IsVisible(item))
                boundingRect = self.GetBoundingRect(item)
                Logger.debug('MediaTreeCtrl.EnsureVisible(): GetBoundingRect()=%s' % boundingRect)
                Logger.debug('MediaTreeCtrl.EnsureVisible(): GetClientSize()=%s' % self.GetClientSize())
                Logger.debug('MediaTreeCtrl.EnsureVisible(): GetClientRect()=%s' % self.GetClientRect())
                Logger.debug('MediaTreeCtrl.EnsureVisible(): GetSize()=%s' % self.GetSize())
                if ((boundingRect == None)
                    or (boundingRect[0] < 0) 
                    or (boundingRect[1] < 0)):  # (not self.IsVisible(args[0])):
#                     previousEntry = self.GetPrevVisible(item)
#                     if (previousEntry.IsOk()):
#                         Logger.debug('MediaTreeCtrl.EnsureVisible: invisible, scrolling to previous %s' % previousEntry)
#                         wx.TreeCtrl.EnsureVisible(previousEntry)
#                     else:
                    Logger.debug('MediaTreeCtrl.EnsureVisible: invisible, scrolling to %s' % entry)
                    wx.TreeCtrl.EnsureVisible(self, *args, **kwargs)
                    wx.TreeCtrl.ScrollTo(self, item)
                    Logger.debug('MediaTreeCtrl.EnsureVisible(): GetBoundingRect() is now %s' % self.GetBoundingRect(item))                    
                else:
                    Logger.debug('MediaTreeCtrl.EnsureVisible(): %s already visible' % entry)
            else:
                Logger.debug('MediaTreeCtrl.EnsureVisible(): No data found for tree item %s' % item)
        else:
            Logger.debug('MediaTreeCtrl.EnsureVisible(): self is a dead object')


    def getDescendants (self, treeItemID):
        """Return the set of all descendants (direct children and, recursively, their descendants) of treeItemID.
        
        wx.TreeCtrl only defines GetFirstChild() and GetNextChild()
        
        wx.TreeItemID treeItemID
        Return Set of all treeItemIDs in self
        """
        result = set()
        child = self.GetFirstChild(treeItemID)[0]
        result.add(treeItemID)  # include item here
        while (child.IsOk()):  # while there are children
            result.update(self.getDescendants(child))  # get child's descendants
            child = self.GetNextSibling(child)  # get next child
        return(result)


    def DeleteAllItems(self):
        """Remove all items. 
        
        Performance of DeleteAllItems() is bad, because the selection is updated after each removal.  
        """
        self.ignoreSelectionChanges = True
        wx.TreeCtrl.DeleteAllItems(self) 
        self.ignoreSelectionChanges = False
        
    
    def OnCompareItems(self, item1, item2):
        """Sorts tree items according to full path name.
        """
        entry1 = self.GetItemData(item1).GetData()
        entry2 = self.GetItemData(item2).GetData()
#         # this will put singles before groups, which is not correct for organization by name
#         if (entry1.isGroup() == entry2.isGroup()):
#             return(cmp(entry1.getPath().lower(), entry2.getPath().lower()))
#         elif (entry1.isGroup()):  # put groups after single media
#             return(1)
#         else:  # entry2 is a group
#             return(-1)
        return(cmp(entry1.getPath().lower(), entry2.getPath().lower()))



# Internal
    def storeExpansionState(self):
        """Store the expansion state of all Groups, to restore after filtering.
        """
        for itemID in self.getDescendants(self.GetRootItem()):
            entry = self.GetItemData(itemID).GetData()
            if (entry <> self.model.getRootEntry()):
                entry.isExpanded = (entry.isGroup()
                                    and self.IsExpanded(itemID))


    def restoreExpansionState(self):
        """Restore the expansion state of all unfiltered Groups after filtering.
        """
        for itemID in self.getDescendants(self.GetRootItem()):
            entry = self.GetItemData(itemID).GetData()
            if (entry <> self.model.getRootEntry()):
                if (entry.isExpanded):
                    self.Expand(itemID)
                else:
                    self.Collapse(itemID)



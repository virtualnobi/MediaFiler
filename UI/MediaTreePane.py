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
from nobi.ObserverPattern import Observer
from nobi.PausableObservable import PausableObservable
## project
import UI
from UI import GUIId
import Model.Image 
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



class MediaTreeCtrl (wx.TreeCtrl, PausableObservable, Observer):
    """The MediaTreeCtrl displays a hierarchy of all media in its model, an ImageFilerModel.

    ObserverPattern aspects:
    selection: the selection changed
    """



# Constants
    Logger = logging.getLogger(__name__)



# section: Lifecycle
    def __init__ (self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TR_DEFAULT_STYLE):
        # initialize superclasses
        wx.TreeCtrl.__init__(self, parent, pos=pos, size=size, style=(style | wx.NO_BORDER | wx.TR_HIDE_ROOT | wx.TR_TWIST_BUTTONS))  # | wx.TR_MULTIPLE 
        Observer.__init__(self)
        PausableObservable.__init__(self, ['selection'])
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
        # internal state
        self.model = None  
        self.selectionBeforeFiltering = None  # selected Entry before filtering started, to detect whether it is filtered
        self.ignoreSelectionChanges = False  # flag to stop onSelectionChanged events when mass deleting



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
                self.__class__.Logger.warning('MediaTreePane.setModel(): Cannot find type icon for class "%s"' % c)
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
        logging.debug('MediaTreeCtrl.setEntry(%s)' % entry.getPath())
#         self.Freeze()
        if (entry == self.model.getRootEntry()):
            entry = self.model.getInitialEntry()
        if (entry.getTreeItemID()):
            self.SelectItem(entry.getTreeItemID())
            result = self.EnsureVisible(entry.getTreeItemID())
            logging.debug('MediaTreeCtrl.setEntry(): EnsureVisible() returns %s' % result)
            if (expand):
                self.Expand(entry.getTreeItemID())                
        else:
            logging.error('MediaTreeCtrl.setEntry(): no tree item ID for "%s"' % entry.getPath())
#         self.Thaw()



# Getters
# Event Handlers
    def onSelectionChanged (self, event):
        """User changed the selection in the tree.
        """
        if (self.ignoreSelectionChanges): 
            pass
        else:
            #logging.debug('MediaTreeCtrl.onSelectionChanged(): Received event %s with item %s' % (event, event.GetItem()))
            entry = self.GetItemData(event.GetItem()).GetData()
            logging.debug('MediaTreeCtrl.onSelectionChanged(): Selecting "%s"' % entry.getPath())
            self.ignoreSelectionChanges = True
            self.model.setSelectedEntry(entry)
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
        #print('User selected context menu item %s' % event.Id)
        wx.BeginBusyCursor()
        message = event.EventObject.currentEntry.runContextMenuItem(event.Id, self)
        if (isinstance(message, basestring)):
            self.GetParent().displayInfoMessage(message)
        wx.EndBusyCursor()



# Inheritance - Observer
    def updateAspect(self, observable, aspect):
        """ASPECT of OBSERVABLE changed. 
        """
        super(MediaTreeCtrl, self).updateAspect(observable, aspect)
        logging.debug('MediaTreeCtrl.updateAspect(%s)' % aspect)
        if (aspect == 'name'):  # name of an Entry changed
            #print('MediaTreeCtrl: name change of %s' % observable)
            node = observable.getTreeItemID()
            self.SetItemText(node, observable.getFilename())
            self.SortChildren(self.GetItemParent(node))
            self.EnsureVisible(node)  # to keep node visible after sorting
        elif (aspect == 'remove'):  # Entry deleted
            #print('MediaTreeCtrl: entry %s removed' % observable)
            observable.removeObserver(self)
            node = observable.getTreeItemID()
            self.Delete(node)
            logging.debug('MediaTreeCtrl.update(): entry "%s" removed' % observable.getPath())
        elif (aspect == 'children'):  # Group changes its children
            node = observable.getTreeItemID()
            currentSelection = self.model.getSelectedEntry()
            self.ignoreSelectionChanges = True
            self.DeleteChildren(node)
            for subEntry in observable.getSubEntries():
                self.addSubTree(subEntry, node)
            self.SortChildren(node)
            self.ignoreSelectionChanges = False
            self.setEntry(currentSelection)
            logging.debug('MediaTreeCtrl.updateAspect(): children of "%s" changed' % observable.getPath())
            logging.debug('MediaTreeCtrl.updateAspect(): selection "%s" restored' % currentSelection.getPath())
        elif (aspect == 'selection'):  # model changed selection
            entry = observable.getSelectedEntry()
            self.ignoreSelectionChanges = True
            self.setEntry(entry)
            self.ignoreSelectionChanges = False
            logging.debug('MediaTreeCtrl.updateAspect(): selected entry "%s"' % entry.getPath())
        elif (aspect == 'startFiltering'):  # filter changed, remember current selection
            self.selectionBeforeFiltering = self.model.getSelectedEntry()
            self.storeExpansionState()
        elif (aspect == 'stopFiltering'):  # filtering done, try to restore selection
            logging.debug('MediaTreeCtrl.updateAspect(): Recreating tree...')
            self.DeleteAllItems()
            self.addSubTree(self.model.getRootEntry(), None)
            if (self.selectionBeforeFiltering <> self.model.getSelectedEntry()):
                self.setEntry(self.model.getSelectedEntry(), expand=True)
            else:
                self.setEntry(self.model.getSelectedEntry())
            self.restoreExpansionState()
            logging.debug('MediaTreeCtrl.updateAspect(): Recreating tree finished')
        else:
            super(self, MediaTreeCtrl).update(observable, aspect)


# Inheritance - wx.TreeCtrl
    def GetDescendants (self, treeItemID):
        """Return the set of all descendants (direct children and, recursively, their descendants) of treeItemID.
        """
        # TODO: why is this needed?
        result = set()
        child = self.GetFirstChild(treeItemID)[0]
        result.add(treeItemID)  # include item here
        while (child.IsOk()):  # while there are children
            result.update(self.GetDescendants(child))  # get child's descendants
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
        return(cmp(entry1.getPath().lower(), entry2.getPath().lower()))



# Internal
    def storeExpansionState(self):
        """Store the expansion state of all Groups, to restore after filtering.
        """
        for itemID in self.GetDescendants(self.GetRootItem()):
            entry = self.GetItemData(itemID).GetData()
            if (entry <> self.model.getRootEntry()):
                entry.isExpanded = (entry.isGroup()
                                    and self.IsExpanded(itemID))


    def restoreExpansionState(self):
        """Restore the expansion state of all unfiltered Groups after filtering.
        """
        for itemID in self.GetDescendants(self.GetRootItem()):
            entry = self.GetItemData(itemID).GetData()
            if (entry <> self.model.getRootEntry()):
                if (entry.isExpanded):
                    self.Expand(itemID)
                else:
                    self.Collapse(itemID)



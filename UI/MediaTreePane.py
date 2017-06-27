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



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
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
# section: Lifecycle
    def __init__ (self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TR_DEFAULT_STYLE):
        # initialize superclasses
        wx.TreeCtrl.__init__(self, parent, pos=pos, size=size, style=(style | wx.NO_BORDER | wx.TR_HIDE_ROOT | wx.TR_TWIST_BUTTONS))
        Observer.__init__(self)
        PausableObservable.__init__(self, ['selection'])
        # define norgy images
        imglist = wx.ImageList(16, 16, True, 2)
        imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, wx.Size (16, 16)))
        imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size (16, 16)))
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
            self.model.removeObserver(self)
        self.model = model
        self.model.addObserverForAspect(self, 'selection')
        self.model.addObserverForAspect(self, 'startFiltering')
        self.model.addObserverForAspect(self, 'stopFiltering')        
        self.DeleteAllItems()
        self.addSubTree(self.model.getRootEntry(), None)
        self.setEntry(self.model.getSelectedEntry())


    def addSubTree (self, entry, parent):
        """Add a tree node for imageFilerEntry ENTRY under wx.TreeItemID PARENT, and recurse to add all descendants.

        Entry entry is the MediaFiler.Entry to add
        wx.TreeItemID parent the node of the subtree to add. If parent is None, entry is the root node. 

        Return the wx.TreeItemID of entry.
        """
        if (entry.filteredFlag):
            print('MediaTreePane.addSubTree(): Ignoring filtered Entry "%s"' % entry.getPath())
            return(None)
        # create a tree item
        item = wx.TreeItemData(entry)
        # insert tree item
        if (entry.isGroup()):  # entry is a Group, add a collapsible node for entry
            if (parent == None):  # entry is root Group
                node = self.AddRoot("All", GUIId.TI_Folder, GUIId.TI_Folder, item)  
            else:   
                node = self.AppendItem(parent, entry.getFilename(), GUIId.TI_Folder, data=item)
            for subentry in entry.getSubEntries():
                if (not subentry.filteredFlag):
                    self.addSubTree(subentry, node)
        else:
            # add a terminal node for entry
            node = self.AppendItem(parent, entry.getFilename(), GUIId.TI_Image, data=item)
        # register as observer for entry
        entry.addObserverForAspect(self, 'name')
        entry.addObserverForAspect(self, 'remove')
        entry.addObserverForAspect(self, 'children')
        # store wx.TreeItemID in entry for reverse lookup
        entry.setTreeItemID(node)
        self.SortChildren(node)
        return(node)


    def setEntry(self, entry):
        """Select the specified entry in the tree.
        """
        if (entry <> self.model.getRootEntry()):
            self.SelectItem(entry.getTreeItemID())



# Getters
# Event Handlers
    def onSelectionChanged (self, event):
        """User changed the selection in the tree.
        """
        #print('MediaTreePane onSelectionChanged')
        if (self.ignoreSelectionChanges): 
            pass
        else:
            entry = self.GetItemData(event.GetItem()).GetData()
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
    def updateAspect (self, observable, aspect):
        """ASPECT of OBSERVABLE changed. 
        """
        super(MediaTreeCtrl, self).updateAspect(observable, aspect)
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
            print('MediaTreeCtrl.update(): entry "%s" removed' % observable.getPath())
        elif (aspect == 'children'):  # Group changes its children
            #print('MediaTreeCtrl: entry "%s" changing children...' % observable.getPath())
            node = observable.getTreeItemID()
            self.ignoreSelectionChanges = True
            self.DeleteChildren(node)
            for subEntry in observable.subEntries:
                self.addSubTree(subEntry, node)
            self.SortChildren(node)
            self.ignoreSelectionChanges = False
            logging.debug('MediaTreeCtrl.update(): children of "%s" changed' % observable.getPath())
        elif (aspect == 'selection'):  # model changed selection
            entry = observable.getSelectedEntry()
            self.ignoreSelectionChanges = True
            self.setEntry(entry)
            self.ignoreSelectionChanges = False
            logging.debug('MediaTreeCtrl.update(): selected entry "%s"' % entry.getPath())
        elif (aspect == 'startFiltering'):  # filter changed, remember current selection
            self.selectionBeforeFiltering = self.model.getSelectedEntry()
        elif (aspect == 'stopFiltering'):  # filtering done, try to restore selection
            logging.debug('MediaTreePane.update(): Recreating tree...')
            self.DeleteAllItems()
            self.addSubTree(self.model.getRootEntry(), None)
            if (self.selectionBeforeFiltering <> self.model.getSelectedEntry()):
                self.SelectEntry(self.model.getSelectedEntry())
                self.Expand(self.model.getSelectedEntry().getTreeItemID())
            logging.debug('MediaTreePane.update(): Recreating tree finished')
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

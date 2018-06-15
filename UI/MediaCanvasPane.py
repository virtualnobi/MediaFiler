# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## standard
import math
import logging
import cProfile, pstats, StringIO
## contributed
import wx
## nobi
from nobi.ObserverPattern import Observer
## project
from UI import GUIId
from Model.Single import ImageBitmap


class MediaCanvas(wx.Panel, Observer):
    """
    """



# Constants
    Logger = logging.getLogger(__name__)
    ImagePadding = 1  # pixel distance between images on canvas in X and Y direction



# Class Variables
# Class Methods
# Lifecycle
    def __init__ (self, parent):
        """Create a new instance, inside window parent.
        
        wx.Window parent
        """
        self.model = None
        # initialize superclasses
        wx.Panel.__init__(self, parent)
        Observer.__init__(self)
        # events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.onClickCanvas)  # mouse events (move, click) to select image
        self.Bind(wx.EVT_MENU_RANGE, self.onContextMenuSelection, id=GUIId.EntryFunctionFirst, id2=GUIId.EntryFunctionLast)  # context menu actions on Entry objects
        # internal state
        self.model = None
        self.entry = None
        self.SetBackgroundColour('white')
        self.ClearBackground()
        (self.width, self.height) = self.GetSizeTuple()


# Getters
# Setters
    def setModel(self, model):
        """
        """
        if (self.model):
            self.model.removeObserver(self)
        self.model = model
        self.model.addObserverForAspect(self, 'selection')
        self.model.addObserverForAspect(self, 'stopFiltering')
        self.lastLeftDownImage = None  # last Image on which left mouse button went down, for selection
        self.lastRightDownImage = None  # last Image on which right mouse button went down, for context menu
        self.rows = 1
        self.cols = 1
        self.setEntryProfiled(self.model.getSelectedEntry())


    def setEntryProfiled(self, entry, forceUpdate=False):
        profiler = cProfile.Profile()
        profiler.enable()
        self.setEntry(entry, forceUpdate)
        profiler.disable()
        resultStream = StringIO.StringIO()
        ps = pstats.Stats(profiler, stream=resultStream)  # .ps.strip_dirs()  # remove module paths
        ps.sort_stats('cumulative')  # sort according to time per function call, including called functions
        ps.sort_stats('time')  # sort according to time per function call, excluding called functions
        ps.print_stats(20)  # print top 20 
        print('Profiling Results for MediaCanvas.setEntry()')
        print(resultStream.getvalue())
        print('---')


    def setEntry(self, entry, forceUpdate=False):
        """Set the entry to display.
        
        Boolean forceUpdate redisplays even if the same entry is already selected (after filtering)
        """
        MediaCanvas.Logger.debug('MediaCanvas.setEntry("%s") with canvas %dx%d' % (entry.getPath(), self.width, self.height))
        if (entry == self.model.root):  # TODO: remove
            MediaCanvas.Logger.error('MediaCanvas.setEntry() should not get model root as entry...')
            entry = self.model.initialEntry
        if (forceUpdate 
            or (self.entry <> entry)):
            wx.BeginBusyCursor()
            self.Freeze() # TODO: must become faster
            column = 1  # count columns when placing images in grid
            (x, y) = (0, 0)  # position of image
            self.clear()  # unbind events and unregister observable
            self.entry = entry
            self.entry.addObserverForAspect(self, 'children')
            displayedEntries = entry.getEntriesForDisplay()
            self.calculateGrid(len(displayedEntries))
            for entry in displayedEntries:  # TODO: use multiprocessing.Pool() or similar
                entry.addObserverForAspect(self, 'name')
                # place image on canvas
                MediaCanvas.Logger.debug('MediaCanvasPane.setEntry(): at pixel (%d, %d) in column %d, placing "%s"' % (x, y, column, entry.getPath()))
                bitmap = ImageBitmap(self, 
                                     -1, 
                                     entry, 
                                     (x + (self.ImagePadding / 2)), 
                                     (y + (self.ImagePadding / 2)), 
                                     self.imageWidth, 
                                     self.imageHeight)
                bitmap.Bind(wx.EVT_MOUSE_EVENTS, self.onClickImage)
                bitmap.Bind(wx.EVT_MENU_RANGE, self.onContextMenuSelection, id=GUIId.EntryFunctionFirst, id2=GUIId.EntryFunctionLast)
                # calculate next image position
                if (column == self.cols): 
                    x = 0
                    y = (y + self.imageHeight + self.ImagePadding)
                    column = 1
                else:  
                    x = (x + self.imageWidth + self.ImagePadding)
                    column = (column + 1)
            self.Thaw()
            self.Refresh()
            self.Update()
            wx.EndBusyCursor()
        MediaCanvas.Logger.debug('MediaCanvas.setEntry() finished')


# Event Handling
    def onClickCanvas(self, event):
        """User clicked the canvas.
        """
        if (self.entry == None):
            pass  # print('CanvasPane.onClickCanvas() with entry being NONE')
        elif (self.entry.getParentGroup() == None):
            pass  # print('CanvasPane.ClickCanvas() on entry "%s" without parent' % self.entry.getPath())
        else:
            self.onClick(event, self.entry)
        
        
    def onClickImage(self, event):
        """User clicked an image. 
        """
        self.onClick(event, event.GetEventObject().getEntry())
        

    def onContextMenuSelection(self, event):
        """User selected an item in a context menu. 
        
        Route to current Entry.
        """
        print('User selected context menu item %s' % event.Id)
        wx.BeginBusyCursor()
        message = event.EventObject.currentEntry.runContextMenuItem(event.Id, self)
        if (isinstance(message, basestring)):
            pass  # TODO: display in status bar
        wx.EndBusyCursor()

    

# Inheritance - ObserverPattern
    def updateAspect(self, observable, aspect):
        """ ASPECT of OBSERVABLE has changed. 
        """
        super(MediaCanvas, self).updateAspect(observable, aspect)
        if (aspect == 'selection'):  # MediaCollection changes selection
            entry = observable.getSelectedEntry()
            self.setEntry(entry)
        elif (aspect == 'stopFiltering'):  # after filtering, redisplay groups
            entry = observable.getSelectedEntry()
            if (entry.isGroup()):
                self.setEntry(entry, forceUpdate=True)
        elif (aspect == 'children'):  # the currently selected Entry has changed children
            self.clear()
            self.setEntry(observable)
        elif (aspect == 'name'):  # an Entry changed its name
            if (observable <> self.entry):  # child of currently selected Entry changed, redisplay to keep order correct
                parent = self.entry
                self.setEntry(parent, forceUpdate=True)


    
# Internal    
    def clear (self):
        """Clear the canvas.
        """
        # unregister from observable
        if (self.entry):
            self.entry.removeObserver(self)
            for entry in self.entry.getEntriesForDisplay():
                entry.removeObserver(self)
        self.entry = None
        # remove images from grid
        for child in self.GetChildren():
            #self.gridSizer.Remove (child)
            child.Unbind(wx.EVT_MOUSE_EVENTS)
            child.Unbind(wx.EVT_MENU_RANGE)
            child.Destroy()
        self.ClearBackground()


    def calculateGrid (self, numberOfImages):
        """Calculate number of rows and columns for given numberOfImages.
        """
        # determine aspect ratio of canvas
        (self.width, self.height) = self.GetSizeTuple()
        ratio = (float(self.width) / float(self.height))
        # calculate number of columns
        if (numberOfImages == 0): # special case - no images, no display
            #self.displayMessage ("No images selected")
            return
        cols = float(numberOfImages) # explore layouts from nx1 grid down to 1xn grid
        while (cols > 0):
            rows = math.ceil(numberOfImages / cols) # how many rows are needed for this many columns
            #print "Checking %dx%d grid for %d entries and ratio %f" % (cols, rows, numberOfImages, ratio)
            if ((cols / rows) >= 1):  # layout wider than tall
                if (ratio >= (cols / rows)):  # first time that window aspect bigger than layout aspect
                    break  # use current number of columns
            else: # layout taller than wide
                if (ratio >= (cols / rows)): 
                    cols = (cols + 1)  # use previous number of columns in last iteration
                    break
            cols = (cols - 1)
        # calculate rows from columns
        if (cols == 0): # while-loop terminated on cols condition
            cols = 1.0 # ensure at least one column
        self.rows = int(math.ceil(numberOfImages / cols)) # ensure floating-point arithmetic: cols is float
        # depending on number of rows, number of cols may be reduced
        self.cols = int(math.ceil(numberOfImages / float (self.rows))) # ensure floating-point arithmetic
        # calculate image size
        self.imageWidth = int((self.width - ((self.cols + 1) * self.ImagePadding)) / self.cols)
        self.imageHeight = int((self.height - ((self.rows + 1) * self.ImagePadding)) / self.rows)
        #print '%d items sized %dx%d placed in %dx%d grid in %dx%d pane' % (numberOfImages, self.imageWidth, self.imageHeight, self.cols, self.rows, self.width, self.height)

        
    def onClick(self, event, target):
        """User clicked the canvas. If this is a valid click (i.e., left up/down on same object), select Entry target.
        """
        #print('MediaCanvasPane onClick on "%s"' % target.getPath())
        if (event.LeftDown()):
            #print('LeftDown on %s' % target.getPath())
            self.lastLeftDownImage = target
        elif (event.LeftUp()):
            #print('LeftUp on %s' % target.getPath())
            if (self.lastLeftDownImage == target):  # mouse down/up on same Image
                if ((target == self.entry)  # clicked on blank area, navigate to parent of self.entry
                    and (target.getParentGroup() <> None)):
                    target = target.getParentGroup()
                #print('Change selection to %s' % target.getPath())
                self.model.setSelectedEntry(target)
            self.lastLeftDownImage = None
        elif (event.RightDown()):
            #print('RightDown on %s' % target.getPath())
            self.lastRightDownImage = target
        elif (event.RightUp()):
            #print('RightUp on %s' % target.getPath())
            if (target == self.lastRightDownImage):
                #print('Context menu on %s' % target.getPath())
                menu = target.getContextMenu()  # create context menu for selected Entry
                self.PopupMenu(menu)  # let user select item, and execute its function
                menu.Destroy()  # clear context menu
                self.lastRightDownImage = None
        else:
            #print('Other mouse event')
            self.lastLeftDownImage = None
            self.lastRightDownImage = None
        
        

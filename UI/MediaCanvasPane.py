# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## standard
import math
import logging
import os.path
import gettext
## contributed
import wx
## nobi
from nobi.ObserverPattern import Observer
from nobi.Memoize import memoize
from nobi.logging import profiledOnLogger
## project
import UI
from UI import GUIId
from Model.Single import MediaBitmap



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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3 
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class MediaCanvas(wx.Panel, Observer):
    """
    """



# Constants
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
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPressed)
        self.Bind(wx.EVT_SIZE, self.onResize)
        # internal state
        self.model = None
        self.entry = None
        self.ignoreNameChanges = False  # ignore observable updates on 'name' aspect
        self.SetBackgroundColour('white')
        self.ClearBackground()
#         (self.width, self.height) = self.GetSizeTuple()
        (self.width, self.height) = self.GetSize()  # Python 3
        self.lastResizeEntry = None
        self.lastResizeSize = self.GetSize()



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
        self.setEntry(self.model.getSelectedEntry())


    @profiledOnLogger(Logger)
    def setEntry(self, entry, forceUpdate=False):
        """Set the entry to display.
        
        Boolean forceUpdate redisplays even if the same entry is already selected (after filtering)
        """
        Logger.debug('MediaCanvas.setEntry("%s") with canvas %dx%d' % (entry.getPath(), self.width, self.height))
        if (forceUpdate 
            or (self.entry != entry)):
            self.clear()  # unbind events and unregister observable
            self.entry = entry
            self.entry.addObserverForAspect(self, 'children')
            displayedEntries = self.entry.getEntriesForDisplay()
            self.sizeAndDisplayEntries(displayedEntries, progressIndicator=wx.GetApp())
        Logger.debug('MediaCanvas.setEntry() finished')


# Event Handling
    def onClickCanvas(self, event):
        """User clicked the canvas.
        """
        if (self.entry == None):
            Logger.error('MediaCanvasPane.onClickCanvas() with entry being NONE')
            pass
        elif (self.entry.getParentGroup() == None):
            Logger.error('MediaCanvasPane.onClickCanvas() on entry without parent "%s"' % self.entry)
            pass
        else:
            self.handleImageClick(event, self.entry)
        
        
    def onClickImage(self, event):
        """User clicked an image. 
        """
        self.handleImageClick(event, event.GetEventObject().getEntry())
        

    def onContextMenuSelection(self, event):
        """User selected an item in a context menu. 
        
        Route to current Entry.
        """
        try:
            event.EventObject.currentEntry
        except: 
            Logger.warning('MediaCanvasPane.onContextMenuSelection(): Attempting repair of currentEntry attribute')
            event.EventObject.currentEntry = event.EventObject.Parent.currentEntry
#        Logger.debug('MediaCanvasPane.onContextMenuSelection(): Received %s for %s' % (event, event.EventObject.currentEntry))
        Logger.debug('MediaCanvasPane.onContextMenuSelection(): Received %s' % event)
        wx.GetApp().startProcessIndicator()
        message = event.EventObject.currentEntry.runContextMenuItem(event.Id, self)
        wx.GetApp().stopProcessIndicator(message)


    def onKeyPressed(self, event):
        Logger.debug('MediaCanvasPane.onKeyPressed(): %s' % event.GetKeyCode())
        wx.PostEvent(self.GetParent(), event)


    def onResize(self, event):
        Logger.debug('MediaCanvasPane.onResize(...')
        (self.width, self.height) = self.GetSize()
        if (self.entry != None):
            if ((self.lastResizeEntry != self.entry) 
                or (self.lastResizeWidth != self.width)
                or (self.lastResizeHeight != self.height)):
                Logger.debug('MediaCanvasPane.onResize(): Recalculation needed')
                self.lastResizeEntry = self.entry
                self.lastResizeWidth = self.width
                self.lastResizeHeight = self.height
                displayedEntries = self.entry.getEntriesForDisplay()
                self.sizeAndDisplayEntries(displayedEntries, progressIndicator=wx.GetApp())
            else:
                Logger.debug('MediaCanvasPane.onResize(): Ignored because size and selection unchanged')
        else:
            Logger.warn('MediaCanvasPane.onResize(): Ignored because no entry to display')


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
            if ((not self.ignoreNameChanges)
                and (observable != self.entry)):  # child of currently selected Entry changed, redisplay to keep order correct
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


    def calculateGrid(self, numberOfImages):
        """Calculate number of rows and columns for given numberOfImages.
        
        int numberOfImages
        """
        if (numberOfImages == 0): # no images, no display
            Logger.warn('MediaCanvasPane.calculateGrid(): No images to display')
            self.cols = 1
            self.rows = 1
        elif (numberOfImages == 1):  # one image, 1x1 grid
            Logger.debug('MediaCanvasPane.calculateGrid(): 1 image, choosing 1x1 grid')
            self.cols = 1
            self.rows = 1
        else:
            (self.width, self.height) = self.GetSize()  # Python 3
            if ((0 == self.width)
                or (0 == self.height)):
                Logger.error('MediaCanvasPane.calculateGrid(): Pane width or height are zero!')
                raise ValueError('Pane width (%s) or height(%s) are zero!' % (self.width, self.height))
            (self.rows, self.cols) = self.calculateGridForSize(numberOfImages, self.width, self.height)  # state-independent part of calculation is memoized for performance
        # calculate image size
        self.imageWidth = int((self.width - ((self.cols + 1) * self.ImagePadding)) / self.cols)
        self.imageHeight = int((self.height - ((self.rows + 1) * self.ImagePadding)) / self.rows)
        Logger.debug('MediaCanvasPane.calculateGrid(): Placing %d items of %dx%d in %dx%d grid on %dx%d pane' % (numberOfImages, self.imageWidth, self.imageHeight, self.cols, self.rows, self.width, self.height))


    @memoize(20)
    def calculateGridForSize(self, numberOfImages, width, height):
        """Calculate number of rows and columns for given numberOfImages, canvas width and canvas height.
        
        This function does not depend on self's internal state and thus can be memoized.
        
        int numberOfImages which is larger than 1
        int width
        int height
        Return (int rows, int cols)
        """
        canvasAspect = (float(width) / float(height))
        Logger.debug('MediaCanvasPane.calculateGridForSize(): For %s entries, canvas size (%dx%d), and canvas aspect %f (w/h)...' % (numberOfImages, width, height, canvasAspect))
        cols = float(numberOfImages)  # explore layouts from nx1 grid down to 1xn grid
        aspectDistance = 1  # distance between image and canvas aspects, to find smaller distance when choosing between nxm and (n-1)x(m+1) grids
        # previousDistance = 1
        while (cols > 1):  # at least one column required
            rows = math.ceil(numberOfImages / cols) # how many rows are needed for this many columns
            # previousDistance = aspectDistance
            aspectDistance = abs(canvasAspect - (cols / rows))
            Logger.debug('MediaCanvasPane.calculateGridForSize(): ...trying %dx%d grid with image aspect %f and aspect distance %f' % (cols, rows, (cols / rows), aspectDistance))
            if ((cols / rows) <= canvasAspect):
                Logger.debug('MediaCanvasPane.calculateGridForSize(): ...image aspect smaller than canvas aspect, found')
                break
            cols = (cols - 1)
        # this math is here again to determine correction 
        rows = math.ceil(numberOfImages / cols)
        previousDistance = aspectDistance
        aspectDistance = abs(canvasAspect - (cols / rows))
        Logger.debug('MediaCanvasPane.calculateGridForSize(): Chose %dx%d grid with image aspect %f and aspect distance %f' % (cols, rows, (cols / rows), aspectDistance))
        if (previousDistance < aspectDistance):
            Logger.debug('MediaCanvasPane.calculateGridForSize(): Select one column more because aspect distance has increased')
            cols = (cols + 1)
        # calculate rows from columns
        rows = int(math.ceil(numberOfImages / cols)) # ensure floating-point arithmetic: cols is float
        # depending on number of rows, number of cols may be reduced
        savedCols = int(cols)
        cols = int(math.ceil(numberOfImages / float(rows))) # ensure floating-point arithmetic
        if (savedCols != cols):
            print('MediaCanvasPane.calculateGridForSize(): Columns corrected to %f' % cols)
        return(rows, cols)



    def sizeAndDisplayEntries(self, entries, progressIndicator=None):
        """Determine size and place of entries and add them to canvas. 

        ProgressIndicator

        psutil.cpu_count() gives too many (= logical) cores
        
        https://wiki.wxpython.org/LongRunningTasks
        
        TODO: refactor for multiprocessing.Pool():
        from multiprocessing import Process, Queue
        def f(q):
            q.put([42, None, 'hello'])
        if __name__ == '__main__':
            q = Queue()
            p = Process(target=f, args=(q,))
            p.start()
            print q.get()    # prints "[42, None, 'hello']"
            p.join()
        """
        self.ignoreNameChanges = True  # stop reacting on observable 'name' changes, because it causes recursion
        # remove images from grid
        for child in self.GetChildren():
            child.Unbind(wx.EVT_MOUSE_EVENTS)
            child.Unbind(wx.EVT_MENU_RANGE)
            child.Destroy()
        self.ClearBackground()
        # 
        if (10 < len(entries)):
            if (progressIndicator):
                progressIndicator.beginPhase(len(entries), (_('Resizing images in "%s"') % self.entry.getIdentifier()))  
                Logger.debug('MediaCanvasPane.sizeAndDisplayEntries(): Using progress indicator %s' % progressIndicator)
        else:  # do not indicate progress for less than 10 entries
            progressIndicator = None  
        column = 1  # count columns when placing images in grid
        (x, y) = (0, 0)  # position of image
        self.calculateGrid(len(entries))
        for entry in entries:
            if (progressIndicator):
                progressIndicator.beginStep()
            entry.addObserverForAspect(self, 'name')  # to reorder images when a name changes
            Logger.debug('MediaCanvasPane.sizeAndDisplayEntries(): at pixel (%d, %d) in column %d, placing "%s"' % (x, y, column, entry.getPath()))
            bitmap = MediaBitmap(self, 
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
        self.Update()
        self.ignoreNameChanges = False


    def handleImageClick(self, event, target):
        """User clicked the canvas. If this is a valid click (i.e., left up/down on same object), select Entry target.
        """
        Logger.debug('MediaCanvasPane.handleImageClick(): on "%s"' % target.getPath())
        if (event.LeftDown()):
            Logger.debug('MediaCanvasPane.handleImageClick(): LeftDown on %s' % target.getPath())
            self.lastLeftDownImage = target
        elif (event.LeftUp()):
            Logger.debug('MediaCanvasPane.handleImageClick(): LeftUp on %s' % target.getPath())
            if (self.lastLeftDownImage == target):  # mouse down/up on same Image
                if ((target == self.entry)  # clicked on blank area, navigate to parent of self.entry
                    and (target.getParentGroup() != None)):
                    target = target.getParentGroup()
                Logger.debug('MediaCanvasPane.handleImageClick(): Change selection to %s' % target.getPath())
                self.model.setSelectedEntry(target)
            self.lastLeftDownImage = None
        elif (event.RightDown()):
            Logger.debug('MediaCanvasPane.handleImageClick(): RightDown on %s' % target.getPath())
            self.lastRightDownImage = target
        elif (event.RightUp()):
            Logger.debug('MediaCanvasPane.handleImageClick(): RightUp on %s' % target.getPath())
            if (target == self.lastRightDownImage):
                Logger.debug('MediaCanvasPane.handleImageClick(): Context menu on %s' % target.getPath())
                menu = target.getContextMenu()  # create context menu for selected Entry
                Logger.debug('MediaCanvasPane.handleImageClick(): Menu''s entry is %s' % menu.currentEntry)
                self.PopupMenu(menu)  # let user select item, and execute its function
                menu.Destroy()  # clear context menu
                self.lastRightDownImage = None
        else:
            Logger.debug('MediaCanvasPane.handleImageClick(): Other mouse event')
            self.lastLeftDownImage = None
            self.lastRightDownImage = None
        
        

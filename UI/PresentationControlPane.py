"""
The PresentationControlPane contains the buttons to control a presentation.

It observes the MediaFilerModel for selection changes.

(c) by nobisoft 2016-
"""


# Imports
## Standard
import threading
import gettext
import os.path
import logging
## Contributed
import wx
## nobi
from nobi.ObserverPattern import Observer
## Project
import UI  # to access UI.PackagePath
from UI import GUIId



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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
def N_(message): return message




class PresentationControlPane(wx.Panel, Observer): 
    """
    """
    

# Constants
    TimerDelayShort = 2  # seconds
    TimerDelayLong = 15 
    LabelMediaName = _('Name')



# Class Variables
    Logger = logging.getLogger(__name__)
    timerDelay = TimerDelayLong



# Class Methods
    @classmethod
    def classMethod(clas):
        """
        """
        pass



# Lifecycle
    def __init__(self, parent):
        """
        """
        # inheritance
        wx.Panel.__init__(self, parent, style=(wx.FULL_REPAINT_ON_RESIZE))
        Observer.__init__(self)
        # internal state
        self.model = None
        self.presentationTimer = None
        # buttons to resume and stop the presentation
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.resumeButton = wx.Button(self, id=GUIId.ResumeSlideshow, label=GUIId.FunctionNames[GUIId.ResumeSlideshow])
        self.resumeButton.Bind(wx.EVT_BUTTON, self.onResumeSlideshow, id=GUIId.ResumeSlideshow)
        self.GetSizer().Add(self.resumeButton, flag=(wx.ALIGN_CENTER_VERTICAL))
        self.stopButton = wx.Button(self, id=GUIId.StopSlideshow, label=GUIId.FunctionNames[GUIId.StopSlideshow])
        self.stopButton.Disable()
        self.stopButton.Bind(wx.EVT_BUTTON, self.onStopPresentation, id=GUIId.StopSlideshow)
        self.GetSizer().Add(self.stopButton, flag=(wx.ALIGN_CENTER_VERTICAL))
        # buttons to show the previous and next image
        button = wx.Button(self, id=GUIId.NextImage, label=GUIId.FunctionNames[GUIId.NextImage])
        button.Bind(wx.EVT_BUTTON, self.onNextImage, id=GUIId.NextImage)
        self.GetSizer().Add(button, flag=(wx.ALIGN_CENTER_VERTICAL))
        button = wx.Button(self, id=GUIId.PreviousImage, label=GUIId.FunctionNames[GUIId.PreviousImage])
        button.Bind(wx.EVT_BUTTON, self.onPreviousImage, id=GUIId.PreviousImage)
        self.GetSizer().Add(button, flag=(wx.ALIGN_CENTER_VERTICAL))
        # text to show the current media name
        self.GetSizer().Add(wx.StaticText(self, -1, ('  %s: ' % self.LabelMediaName)), flag=wx.ALIGN_CENTER_VERTICAL)
        self.mediaName = wx.StaticText(self, -1, '(none)')
        self.GetSizer().Add(self.mediaName, flag=wx.ALIGN_CENTER_VERTICAL)
        self.GetSizer().Add(wx.StaticText(self, -1, '  '), flag=wx.ALIGN_CENTER_VERTICAL)
        # buttons to control presentation duration
        self.quickButton = wx.Button(self, id=GUIId.QuickSlideshow, label=GUIId.FunctionNames[GUIId.QuickSlideshow])
        self.quickButton.Enable()
        self.quickButton.Bind(wx.EVT_BUTTON, self.onChangeDuration, id=GUIId.QuickSlideshow)
        self.GetSizer().Add(self.quickButton, flag=(wx.ALIGN_CENTER_VERTICAL))
        self.slowButton = wx.Button(self, id=GUIId.SlowSlideshow, label=GUIId.FunctionNames[GUIId.SlowSlideshow])
        self.slowButton.Disable()
        self.slowButton.Bind(wx.EVT_BUTTON, self.onChangeDuration, id=GUIId.SlowSlideshow)
        self.GetSizer().Add(self.slowButton, flag=(wx.ALIGN_CENTER_VERTICAL))



# Setters
    def setModel(self, aMediaCollection):
        """Store a MediaCollection. 
        """
        if (self.model):
            self.model.removeObserver(self)
        self.model = aMediaCollection
        self.model.addObserverForAspect(self, 'selection')
        self.setEntry(self.model.getSelectedEntry())

    
    def setEntry(self, anEntry):
        """Store anEntry as the selected entry. 
        """
        self.entry = anEntry
        self.mediaName.SetLabel(self.entry.getOrganizationIdentifier())
        self.GetSizer().Layout()


    def setPresentationDuration(self, seconds):
        """Set the duration to present an image to the specified number of seconds
        """
        self.timerDelay = seconds



# Getters
# Event Handlers
    def onPreviousImage(self, event):  # @UnusedVariable
        """Select the previous media.
        """
        self.onStopPresentation(event)
        self.model.setSelectedEntry(self.model.getSelectedEntry().getPreviousEntry())


    def onNextImage(self, event):  # @UnusedVariable
        """Select the next media.
        """
        self.model.setSelectedEntry(self.model.getSelectedEntry().getNextEntry())


    def onResumeSlideshow(self, event):  # @UnusedVariable
        """Start the presentation.
        """
        self.resumeButton.Disable()
        self.stopButton.Enable()
        self.presentNext()


    def onStopPresentation(self, event):  # @UnusedVariable
        """Stop the running presentation.
        """
        if (self.presentationTimer):
            self.__class__.Logger.debug('PresentationController.onStopPresentation(): Stopping %s' % self.presentationTimer)
            self.presentationTimer.cancel()
            self.presentationTimer = None
        self.stopButton.Disable()
        self.resumeButton.Enable()


    def onChangeDuration(self, event):
        """Change the presentation duration for an image (faster or slower, depending on button pressed).
        """
        if (event.GetId() == GUIId.QuickSlideshow):
            self.setPresentationDuration(self.TimerDelayShort)
            self.quickButton.Disable()
            self.slowButton.Enable()
        else:
            self.setPresentationDuration(self.TimerDelayLong)
            self.slowButton.Disable()
            self.quickButton.Enable()



# Inheritance - ObserverPattern        
    def updateAspect(self, observable, aspect):
        """
        """
        super(PresentationControlPane, self).updateAspect(observable, aspect)
        if (aspect == 'selection'):
            self.setEntry(observable.getSelectedEntry())



# Other API Functions
    def presentNext(self):
        """Present the next media, and schedule the next run of this function. 
        """
        self.model.setSelectedEntry(self.model.getNextEntry(self.model.getSelectedEntry()))
        self.presentationTimer = threading.Timer(self.timerDelay, self.presentNext)
        self.presentationTimer.start()
        self.__class__.Logger.debug('PresentationController.presentNext(): Scheduled timer %s to show next image in %s secs' % (self.presentationTimer, self.timerDelay))



# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



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
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
    print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message




class PresentationControlPane(wx.Panel, Observer): 
    """
    """
    

# Constants
    TimerDelayShort = 2  # seconds
    TimerDelayLong = 15 
    LabelMediaName = _('Name')



# Class Variables
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
    def setModel(self, aMediaFilerModel):
        """Observe the model for selection changes
        """
        if (self.model):
            self.model.removeObserver(self)
        self.model = aMediaFilerModel
        if (self.model):
            self.model.addObserverForAspect(self, 'selection')

    

    def setPresentationDuration(self, seconds):
        """Set the duration to present an image to the specified number of seconds
        """
        self.timerDelay = seconds



# Getters
    def getAttribute(self):  # inherited from SuperClass
        """
        """
        pass
    
    

# Event Handlers
    def onPreviousImage(self, event):  # @UnusedVariable
        self.onStopPresentation(event)
        self.model.setSelectedEntry(self.model.getPreviousEntry(self.model.getSelectedEntry()))


    def onNextImage(self, event):  # @UnusedVariable
        self.model.setSelectedEntry(self.model.getNextEntry(self.model.getSelectedEntry()))


    def onResumeSlideshow(self, event):  # @UnusedVariable
        self.resumeButton.Disable()
        self.stopButton.Enable()
        self.presentNext()


    def onStopPresentation(self, event):  # @UnusedVariable
        if (self.presentationTimer):
            print('Stopping %s' % self.presentationTimer)
            self.presentationTimer.cancel()
            self.presentationTimer = None
        self.stopButton.Disable()
        self.resumeButton.Enable()


    def onChangeDuration(self, event):
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
            self.mediaName.SetLabel(observable.getSelectedEntry().getFilename())
            self.GetSizer().Layout()
            pass



# Other API Functions
    def presentNext(self):
        """
        """
        self.model.setSelectedEntry(self.model.getNextEntry(self.model.getSelectedEntry()))
        print('Scheduling next image in %s secs' % self.timerDelay)
        self.presentationTimer = threading.Timer(self.timerDelay, self.presentNext)
        self.presentationTimer.start()
        print('Started %s' % self.presentationTimer)



# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass



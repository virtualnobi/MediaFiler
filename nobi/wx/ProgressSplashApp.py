#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
from __future__ import print_function
import time
## Contributed
import wx
## nobi
## Project


class ProgressSplashApp(wx.App):
    """A wx.App which shows a splash screen with a progress indicator and phase string.
    
    Use a background image with white background in lower area, as the wx.StaticText used for the
    phase text does not allow a transparent background, and so is set to white. 
    
    Override OnInit() and call SetProgress(percent, text) for loading indicator.
    """



# Constants
# Class Variables
# Class Methods
# Lifecycle
    def OnInit(self, splashFilename=None):
        """Display a splash screen including loading indicator. 
         
        Override in subclass and use SetProgress() to update the loading indicator.
        Remember to call ProgressSplashApp.OnInit() at the beginning of the subclass method.
        
        String splashFilename names a BMP bitmap to show as splash image.
        Return True
        """
        if (splashFilename):
            splashBitmap = wx.Bitmap(splashFilename, wx.BITMAP_TYPE_BMP)
            width, height = splashBitmap.GetSize()
            if ((0 < width) and
                (0 < height)):
                self.splashScreen = wx.SplashScreen(splashBitmap,
                                                    (wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT),
                                                    1,  # timeout must be integer, but is ignored due to SPLASH_NO_TIMEOUT 
                                                    None, 
                                                    -1, 
                                                    wx.DefaultPosition, 
                                                    wx.DefaultSize,
                                                    wx.BORDER_SIMPLE)
                self.splashText = wx.StaticText(self.splashScreen,
                                                -1,
                                                label='Processing...',
                                                pos=(5, (height - 30)),
                                                size=((width - 10), 20))
                self.splashText.SetBackgroundColour('white')
                self.splashGauge = wx.Gauge(self.splashScreen, 
                                            -1,
                                            pos=(0, (height-10)),
                                            size=(width, 10), 
                                            range=100)
                wx.Yield()
        return(True)



# Setters
    def SetProgress(self, percent, phase=None):
        """Set the progress of loading to percent (0..100).
        
        Shall be called during wx.App.OnInit() to display loading progress.
        Will close the splash screen and show the app's top window is called with percent above 100. 
        
        Number percent indicates completion of loading, use 101 to close splash screen
        String phase describes the phase currently running
        """
        if (phase == None):
            phase = ('Processing... %d%%' % percent)
        self.splashText.SetLabel(phase)
        percent = int(percent)
        if (percent < 0):
            raise KeyError
        elif (percent < 100):
            try:
                self.splashGauge.SetValue(percent)
            except: 
                pass
            wx.Yield()
            time.sleep(0.5)
        else:  # 100 < percent
            try: 
                self.splashScreen.Close()
            except:
                pass
            self.GetTopWindow().Show()



# Getters
# Event Handlers
# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
#     import time
    steps = 10
    
    
    class TestApp(ProgressSplashApp):
        def OnInit(self):
            global timer
            ProgressSplashApp.OnInit(self, 'ProgressSplashApp.bmp')
            for step in xrange(1, steps):
                print(step)
                self.SetProgress(int(step * (100 / steps)))
                time.sleep(0.1)
            frame = wx.Frame(None, title='A Splashed Gauge')
            self.mainGauge = wx.Gauge(frame, -1, range=100)
            self.percent = 0
            self.ringTwice(None)
            self.SetTopWindow(frame)
            frame.Bind(wx.EVT_TIMER, self.ringTwice)
            timer = wx.Timer(frame)
            timer.Start(100)
            print('Top window set to %s' % frame)
            self.SetProgress(101)
            return(True)
    
    
        def ringTwice(self, event):  # @UnusedVariable
            print('ring ring %d' % self.percent)
            self.mainGauge.SetValue(self.percent)
            if (100 < self.percent):
                wx.GetApp().Exit()
            self.percent = (self.percent + 10)
    
    
    app = TestApp(False)
    app.MainLoop()



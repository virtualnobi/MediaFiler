#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
# from __future__ import print_function
import time
## Contributed
import wx
# from wx.adv import SplashScreen
import wx.adv
## nobi
from nobi.wx.PhasedProgressBar import PhasedProgressBar 
## Project


class ProgressSplashApp(wx.App):
    """A wx.App which shows a splash screen with a progress indicator and phase name.
    
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
         
        Override in subclass and call ProgressSplashApp.OnInit() at the beginning of the subclass method.

        There are two methods for progress calculation. Both shall be called during OnInit, and shall not be mixed:
        - Use SetProgress() if the percentages can be calculated directly. 
        - Use beginPhase() and beginStep() for more complex calculations, see PhasedProgressBarNew for details.

        String splashFilename names a BMP bitmap to show as splash image.
        Return True
        """
        if (splashFilename):
            splashBitmap = wx.Bitmap(splashFilename, wx.BITMAP_TYPE_BMP)
            width, height = splashBitmap.GetSize()
            if ((0 < width) and
                (0 < height)):
                self.splashScreen = wx.adv.SplashScreen(splashBitmap,
                                                        (wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT),
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
                                                size=((width - 10), (20)))
                self.splashText.SetBackgroundColour('white')
                self.progressBar = PhasedProgressBar(self.splashScreen, 
                                            -1,
                                            pos=(0, (height-10)),
                                            size=(width, 10), 
                                            range=100)
                wx.SafeYield()
        self.currentPercentage = 0.0
        self.remainingStops = [0.0, 100.0]
        return(True)



# Setters
    def SetProgress(self, percent, phase=None):
        """Set the progress of loading to percent (0..100).
    
        Shall be called during wx.App.OnInit() to display loading progress.
        Will close the splash screen and show the app's top window if called with percent <= 100. 
        
        Raises ValueError if progress bar would move backwards
        Number percent indicates completion of loading, use 101 to close splash screen
        String phase is displayed above progress bar
        """
        if (phase == None):
            phase = ('(Processed %d%%)' % percent)
        phase = '%s (%s%%, remaining stops %s)' % (phase, percent, self.getProgressBar().remainingStops)
        print(phase)
        self.splashText.SetLabel(phase)
        percent = int(percent)
        if (percent < self.getProgressBar().GetValue()):
            raise ValueError('Progress bar cannot run backwards (%s smaller than current progress %s)' % (percent, self.getProgressBar().GetValue()))
        elif (percent < 100):
            try:
                self.getProgressBar().SetValue(percent)
            except: 
                pass
            wx.SafeYield()  # doing wx.Yield() twice does not help; time.sleep(1) does not help
            # print('=%s' % self.progressBar.GetValue())
        else:  # 100 <= percent
            try: 
                self.splashScreen.Close()
            except:
                pass
            self.GetTopWindow().Show()


    def beginPhase(self, numberOfSteps, description=''):
        """Begin a new phase consisting of the given number of steps.
        
        int numberOfSteps
        String description displayed as description of the first step
        """
        print('begin phase %s (%s)' % (numberOfSteps, self.getProgressBar()))
        self.getProgressBar().beginPhase(numberOfSteps)
        if (description == ''):
            description = (_('(was: %s') % self.getProgressText().GetLabel())
        self.getProgressText().SetLabel(description)
        self.getProgressText().Show()
        wx.GetApp().ProcessPendingEvents()
        wx.SafeYield()


    def beginStep(self, description=''):
        """Begin a new step, i.e., display its description and advance the progress bar to signal completion of previous step. 
        
        String description displayed as description of the next step
        """
        print('begin step %s (%s)' % (description, self.getProgressBar()))
        self.getProgressBar().beginStep()
        self.getProgressBar().Show()
        description = self.getPhaseDescription(description)
        self.getProgressText().SetLabel(description)
        self.getProgressText().Show()
        wx.GetApp().ProcessPendingEvents()
        wx.SafeYield()


    def finish(self, description=''):
        """
        """
        print('finish (%s)' % self.getProgressBar())
        self.getProgressBar().finish()
        description = self.getPhaseDescription(description)
        self.getProgressText().SetLabel(description)
        self.splashScreen.Close()
        self.GetTopWindow().Show()



# Getters
    def getPhaseDescription(self, description):
        """Return description with added internal state.
        
        String description
        Return String
        """
        if ((description == None)
            or (description == '')):
            description = 'Processing...'
        description = '%s (%s)' % (description, self.getProgressBar())
        return(description)

        
    def getProgressText(self):
        """Return an object to show the step descriptions.
        
        Returns an object with a SetLabel(string) method.
        """
        return(self.splashText)


    def getProgressBar(self):
        """Return an object to show the progress.
        
        Returns an object with beginPhase(Number), beginStep(string), finish(string) methods. 
        """
        return(self.progressBar)



# Event Handlers
# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
# Class Initialization
# Executable Script
if __name__ == "__main__":

    
    class TestProgressSplashApp(ProgressSplashApp):
        def OnInit(self):
            ProgressSplashApp.OnInit(self, 'ProgressSplashApp.bmp')
            self.testPhase(4)
            self.Exit()
            return(True)
     
     
        def testPhase(self, steps):
            ppb = self.getProgressBar()
            ppb.beginPhase(steps)
            for step in range(steps):
                if ((step == 2)
                    or (step == 3)):
                    self.testPhase(step)
                else:
                    ppb.beginStep('Phase with %s steps, at Step %s' % (steps, (step +1)))
                    time.sleep(steps)


    app = TestProgressSplashApp(False)
    app.MainLoop()



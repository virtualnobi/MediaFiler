#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2019-
"""


# Imports
## Standard
from __future__ import print_function
import logging
#import time
## Contributed
import wx 
## nobi
## Project



# Package Variables
Logger = logging.getLogger(__name__)



class PhasedProgressBar(wx.Gauge):
    """A progress bar for processes with a hierarchy of steps, consisting of an unknown number of steps.
    
    Progress is calculated based on the completion of steps, where the beginning of a step implicitly 
    terminates the previous steps and increases the progress bar accordingly. The next step can be divided 
    dynamically into a number of sub-steps, allowing to represent a hierarchy of steps. Step duration is 
    calculated as floating-point numbers for precision. The initial state assumes one step with 100%
    duration, i.e., calling finish() immediately will move the progress bar to completion.
    
    A new step is begun by calling beginStep(). This increases the progress bar to signal the completion of
    the previous step. 
    
    When the next steps consists of N substeps, call beginPhase(N). This splits the duration of the next
    step into N equal parts, which are again started by beginStep(). 
    
    To ensure completion, call finish() to move the progress bar to completion.

    For example:
                     0%    initialized with one step of 100% duration
    beginPhase(3)    0%    duration of next step (100%) is split into 3 steps with 33% each
    beginStep()      0%    begin first step
    beginPhase(2)    0%    duration of next step (33%) is split into 2 steps of 16% each
    beginStep()     33%    begin first embedded step, finish first step of initial 3 steps
    beginStep()     49%    begin second embedded step, finish first step of embedded steps
    beginStep()     65%    begin third step of initial 2 steps, finish second embedded step
    finish()       100%    move to completion

    Unfortunately, the background of wx.StaticText cannot be transparent, and the foreground color of the wx.Gauge 
    cannot be set (or queried). That's why this control does not display a step description as well. 
    
    Inspired by Dragon Energy's answer to my question here:
    https://softwareengineering.stackexchange.com/questions/382003/how-to-calculate-overall-progress-in-independent-phases
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, *args, **kwargs):
        """
        """
        # inheritance
        kwargs['range'] = 100
        if ('style' in kwargs):
            style = (wx.TRANSPARENT_WINDOW | kwargs['style'])
        else:
            style = wx.TRANSPARENT_WINDOW
        kwargs['style'] = style
        super(PhasedProgressBar, self).__init__(*args, **kwargs)
        # internal state
        self.restart()



# Setters
    def restart(self):
        """Reset the progress bar to the beginning.
        """
        self.currentPercentage = 0.0  # use float for correct calculation
        self.remainingStops = [0.0, 100.0]
        self.SetValue(0)



# Getters
    def __repr__(self):
        return('PhasedProgressBar(%s%%, %s remaining)' % (self.currentPercentage, self.remainingStops))



# Other API
    def beginPhase(self, numberOfSteps):
        """Begin a new phase consisting of the given number of steps.

        For each call to this method, beginStep() should be called numberOfSteps times.

        int numberOfSteps must be larger than 1, indicates number of steps in new phase
        """
        if ((not isinstance(numberOfSteps, int))
            or (numberOfSteps < 1)):
            raise ValueError, 'numberOfSteps must be an integer larger than 1'
        if (len(self.remainingStops) < 2):
            raise RuntimeError, 'PhasedProgressBar.beginPhase() called after completion (maybe beginStep() called too often)'
        phaseDuration = (self.remainingStops[1] - self.remainingStops[0])
        stepDuration = (phaseDuration / numberOfSteps)
        for i in range(1, numberOfSteps):
            self.remainingStops.insert(i, (self.remainingStops[0] + (i * stepDuration)))


    def beginStep(self):
        """Begin a step, i.e., advance the progress bar to signal completion of the previous step.
        """
        if (len(self.remainingStops) < 2):
            raise RuntimeError, 'PhasedProgressBar.beginStep() called after completion (maybe called too often)'
        self.currentPercentage = self.remainingStops.pop(0)
        self.SetValue(int(self.currentPercentage))


    def finishStep(self):
        self.beginStep()


    def finish(self):
        """Finish the progress bar. 
        """
        self.remainingStops = []
        self.SetValue(100)



    def SetValue(self, percentage):
        """Set the progress bar to the given percentage, and display it. 
        
        This is about being as real-time as possible; 
        wx delays screen updates to lag up to two invocations after this call.
        """
        # print('Set to %s' % percentage)
        super(PhasedProgressBar, self).SetValue(percentage)
        self.Show()
        wx.GetApp().ProcessPendingEvents()
        wx.SafeYield()  # will disable user input, then execute wx.Yield(), then reenable user input


        
# Event Handlers
# Internal - to change without notice
# Class Initialization
# Executable Script
if __name__ == "__main__":
    import time

    class MyFrame(wx.Frame):
        def __init__(self, parent):
            wx.Frame.__init__(self, parent, -1, "PhasedProgressBar Demo")
            panel = wx.Panel(self)
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.button = wx.Button(panel, -1, label='Start')
            self.Bind(wx.EVT_BUTTON, self.onButton)
            sizer.Add(self.button, flag=wx.ALIGN_CENTER_VERTICAL)
            self.ppb = PhasedProgressBar(panel, -1)
            sizer.Add(self.ppb, proportion=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL), border=0)
            panel.SetSizerAndFit(sizer)
            
        def onButton(self, event):  # @UnusedVariable
            self.ppb.restart()
            self.run()

        def run(self):
            self.ppb.beginPhase(4)
            time.sleep(1)
            self.ppb.beginStep()
            time.sleep(1)
            self.ppb.beginStep()
            steps = 5
            self.ppb.beginPhase(steps)
            for x in range(steps):  # @UnusedVariable
                self.ppb.beginStep()
                print('At Embedded Step %s' % x)
            time.sleep(1)
            self.ppb.beginPhase(2)
            time.sleep(1)
            self.ppb.beginStep()
            time.sleep(1)
            self.ppb.beginStep()
            try:
                self.ppb.beginStep()
            except RuntimeError:
                print('Caught RuntimeError resulting from surplus call to beginStep()')
            self.ppb.finish()

    app = wx.App(0)
    frame = MyFrame(None)
    app.SetTopWindow(frame)
    wx.Yield()
    frame.Show()
    app.MainLoop()
    app.Exit()



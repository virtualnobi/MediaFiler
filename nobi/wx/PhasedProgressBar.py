#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2019-
"""


# Imports
## Standard
from __future__ import print_function
import logging
## Contributed
import wx 
## nobi
## Project



# Package Variables
Logger = logging.getLogger(__name__)



class PhasedProgressBar(wx.Gauge): 
    """A progress bar for processes with a hierarchy of steps, consisting of an unknown number of steps.
    
    To separate the remaining processing time into N steps, call BeginPhase(N). This will split the processing
    time of the current step into N equal sub-steps. A call to BeginPhase() thus represents the beginning of an 
    embedded phase with the specified sub-steps. 
    
    To show completion of a step, call FinishStep(). This will advance the progress bar accordingly. Once the
    process is completed (i.e., 100% are reached), further calls to FinishStep() raise RuntimeError.
    
    For example:
    BeginPhase(3)    0%    remaining progress (100%) is split into 3 steps with 33% each
    FinishStep()    33%    first step completed
    BeginPhase(2)   33%    remaining progress of current step (33%) is split into 2 steps with 16% each
    FinishStep()    49%    finish first step of embedded phase
    FinishStep()    66%    finish second step of embedded phase
    FinishStep()   100%    finish third step of main phase
    
    As can be seen from the percentages, only integer percentages are used and any rounding differences are added 
    to the last step in a phase. 
    
    The initial state assumes one step, i.e., calling FinishStep() once will move the progress bar to completion.
    
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
        # internal state, all calculated as float for precision
        self.currentPercentage = 0.0
        self.remainingStops = [100.0]  



# Setters
    def restart(self):
        """Reset the progress bar to the beginning.
        
        Kept for testing, not recommended for practical use.
        """
        self.currentPercentage = 0.0
        self.remainingStops = [100.0]
        self.SetValue(0)


# Getters
# Other API
    def beginPhase(self, numberOfSteps):
        """Begin a new phase consisting of the given number of steps.

        For each call to this method, FinishStep() must be called numberSteps times.

        int numberOfSteps must be larger than 1, indicates number of steps in new phase
        """
        print('PhasedProgressBar.BeginPhase(): %s steps' % numberOfSteps)
        if ((not isinstance(numberOfSteps, int))
            or (numberOfSteps < 1)):
            raise ValueError, 'numberOfSteps must be an integer larger than 1'
        if (len(self.remainingStops) < 1):
            raise RuntimeError, 'BeginPhase() called after completion (maybe FinishStep() called too often)'
        phaseDuration = (self.remainingStops[0] - self.currentPercentage)
        stepDuration = (phaseDuration / numberOfSteps)
        print('PhasedProgressBar.BeginPhase(): phase is %s%%, step is %s%%' % (phaseDuration, stepDuration))
        for i in range(1, numberOfSteps):
            self.remainingStops.insert((i - 1), (self.currentPercentage + (i * stepDuration)))
        print('PhasedProgressBar.BeginPhase(%s) results in %s+%s' % (numberOfSteps, self.currentPercentage, self.remainingStops))


    def finishStep(self):
        """Finish a step, i.e., advance the progress bar to signal completion of the step.
        """
        print('PhasedProgressBar.FinishStep()')
        if (len(self.remainingStops) < 1):
            raise RuntimeError, 'FinishPhase() called after completion (maybe FinishStep() called too often)'
        self.currentPercentage = self.remainingStops.pop(0)
        self.SetValue(int(self.currentPercentage))
        print('PhasedProgressBar.FinishStep(): current %s%%, remaining %s' % (self.currentPercentage, self.remainingStops))
        # the following is about being as real-time as possible; 
        # wx delays screen updates to lag up to two invocations after FinishStep()
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
            wx.Frame.__init__(self, parent, -1, "PyGauge Demo")
            panel = wx.Panel(self)
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.button = wx.Button(panel, -1, label='Start')
            self.Bind(wx.EVT_BUTTON, self.onButton)
            sizer.Add(self.button, flag=wx.ALIGN_CENTER_VERTICAL)
            self.ppb = PhasedProgressBar(panel, -1)
            sizer.Add(self.ppb, proportion=0, flag=(wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL), border=0)
            panel.SetSizerAndFit(sizer)
            
        def onButton(self, event):
            self.ppb.restart()
            self.run()

        def run(self):
            self.ppb.beginPhase(5)
            time.sleep(1)
            self.ppb.finishStep()
            time.sleep(1)
            self.ppb.finishStep()
            steps = 20
            self.ppb.beginPhase(steps)
            for x in range(steps):  # @UnusedVariable
                self.ppb.finishStep()
            time.sleep(1)
            self.ppb.finishStep()
            self.ppb.beginPhase(2)
            time.sleep(1)
            self.ppb.finishStep()
            time.sleep(1)
            self.ppb.finishStep()
            try:
                self.ppb.finishStep()
            except RuntimeError:
                print('Caught RuntimeError resulting from surplus call to FinishStep()')

    app = wx.App(0)
    frame = MyFrame(None)
    app.SetTopWindow(frame)
    wx.Yield()
    frame.Show()
    # frame.run()
    app.MainLoop()
    app.Exit()



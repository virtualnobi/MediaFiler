#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
from __future__ import print_function
import time
#import unittest
#import datetime
## Contributed
## nobi
from nobi.wx.ProgressSplashApp import ProgressSplashApp
## Project



class TestProgressSplashApp(ProgressSplashApp):
    """
    """
    def OnInit(self):
        """
        """
        ProgressSplashApp.OnInit(self, 'ProgressSplashApp.bmp')
        self.testPhase(2)
        self.Exit()
        return(True)


    def testPhase(self, steps):
        self.BeginPhase(steps)
        for step in range(steps):
            self.BeginStep('Phase with %s steps, Step %s' % (steps, step))
            if (((steps == 4) and (step == 0))
                or ((steps == 3) and (step == 1))):
                self.testPhase(steps - 1)
            else:
                time.sleep(5)



# section: Executable script
if __name__ == "__main__":
    app = TestProgressSplashApp(False)
    app.MainLoop()


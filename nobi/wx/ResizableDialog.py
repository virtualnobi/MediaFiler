"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
## Contributed
import wx
## nobi
## Project


# Class 
class ResizableDialog(wx.Dialog):
    """An extension of wx.Dialog 
    - which supports resizing by the user
    """



# Lifecycle
    def __init__(self, **kwargs):
        if (not 'style' in kwargs):
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE
        kwargs['style'] = (kwargs['style'] | wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, **kwargs)
#         self.Bind(wx.EVT_SIZING, self.onResize)




# Setters
    def onResize(self, event):
        sizer = event.GetEventObject().GetSizer()
        sizer.Layout()
        sizer.Fit(self)

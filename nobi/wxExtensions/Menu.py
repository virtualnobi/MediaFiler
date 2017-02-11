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
class Menu(wx.Menu):
    """An extension of wx.Menu which allows to insert a menu item after another one identified by ID.
    """



# Setters
    def insertAfterId(self, anchorId, newText=None, newId=None, newMenu=None):
        """Add an item after the item with anchorId. 
        
        If neither newId or newMenu are given, a separator is inserted.
        
        Raise ValueError if both newId and newMenu are given, or either is given without newText. 
        Raise KeyError if anchorId does not exist.
        
        Number anchorId is the id of the item after which the new one shall be inserted
        String newText is the text shown in the menu
        Number newId, if given, is the function ID of the new item
        wxExtensions.Menu newMenu, if given, is the next-level menu
        """
        if (newId and newMenu):
            raise ValueError
        if ((not newText) 
            and (newId or newMenu)):
            raise ValueError
        items = self.GetMenuItems()
        itemNo = 0
        for item in items:
            if (item.GetId() == anchorId):
                break
            itemNo = (itemNo + 1)
        if (len(items) <= itemNo):
            raise KeyError
        else:
            if (newId):
                self.Insert((itemNo + 1), newId, newText, kind=wx.ITEM_NORMAL)
            elif (newMenu):
                self.InsertMenu((itemNo + 1), 0, newText, newMenu)  # invent an ID for wxPython
            else:
                self.InsertSeparator(itemNo + 1)


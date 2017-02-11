"""
(c) by nobisoft 2015-
"""


# Imports
## standard
import sys
import os.path
#import glob
import subprocess
## contributed
import wx
## nobi
## project
from UI import GUIId
from .Entry import Entry
from .Single import Single



# Class 
class Image(Single):
    """A Single representing an image file.
    """



# Constants
    LegalExtensions = ['jpg', 'png', 'gif', 'tif']
    PreviewImageFilename = 'Image.jpg'
    
    

## Inheritance - Entry
    @classmethod
    def getLegalExtensions(self):
        """Return a set of file extensions which clas can display.
        
        File extensions are lower-case, not including the preceeding dot.
        
        Returns a Set of Strings.
        """
        return(set(self.LegalExtensions))



# Lifecycle
    def __init__ (self, model, path):
        """Create an Image from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        Single.__init__(self, model, path)
        # internal state
        self.width = 0  # image size
        self.height = 0
        self.rawImage = None
        self.bitmap = None
        return(None)


## Inheritance - Entry
    def runContextMenuItem(self, menuId, parentWindow):
        """User selected menuId from context menu on self. Execute this function.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Return String to display as status
            or None
        """
        print('Image.runContextMenu: %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.StartExternalViewer):
            codec = sys.getfilesystemencoding()
            filename = self.getPath().encode(codec)
            try:
                subprocess.call(['i_view32.exe', filename, '/fs'], shell=True)
            except:
                print('Cannot invoke IrfanView on "%s"!' % filename)
        else:
            return(super(Image, self).runContextMenuItem(menuId, parentWindow))

    

## Inheritance - Single
    def isIdentical(self, anEntry):
        """Check whether self and anEntry have the same content.
        """
        if (super(Image, self).isIdentical(anEntry)):
            return(self.getRawImage().GetData() == anEntry.getRawImage().GetData())
        else:
            return(False)


    def getRawImage(self, debug=False):
        """Retrieve raw data (JPG or PNG or GIF) for image.
        """
        if (not self.rawImage):  # lazily load raw image
            #print('Image.getRawImage(%s)' % self.getPath())
            if (self.getExtension() == 'jpg'):
                self.rawImage = wx.Image(self.getPath(), wx.BITMAP_TYPE_JPEG)
                if (debug and not self.rawImage):
                    print('Failed to load JPG "%s"' % self.getPath())
            elif (self.getExtension() == 'png'):
                self.rawImage = wx.Image(self.getPath(), wx.BITMAP_TYPE_PNG)
                if (debug and not self.rawImage):
                    print('Failed to load JPG "%s"' % self.getPath())
            elif (self.getExtension() == 'gif'):
                self.rawImage = wx.Image(self.getPath(), wx.BITMAP_TYPE_GIF)
                if (debug and not self.rawImage):
                    print('Failed to load JPG "%s"' % self.getPath())
            elif (self.getExtension() == 'tif'):
                self.rawImage = wx.Image(self.getPath(), wx.BITMAP_TYPE_TIF)
                if (debug and not self.rawImage):
                    print('Failed to load JPG "%s"' % self.getPath())
            else: 
                print('Image: Illegal extension in file "%s", using preview image' % self.getPath())
            if (self.rawImage == None):
                self.rawImage = wx.Image(os.path.join(self.model.rootDirectory, '..', 'lib', self.PreviewImageFilename),
                                         wx.BITMAP_TYPE_JPEG)
            assert (self.rawImage <> None), ('Cannot load "%s"' % self.getPath())
            # derive size from raw data
            try:
                self.rawWidth = self.rawImage.GetWidth()
                self.rawHeight = self.rawImage.GetHeight()
            except:
                print('Image: Cannot determine size of "%s", using preview image' % self.getPath())
                self.rawImage = wx.Image(os.path.join(self.model.rootDirectory, '..', 'lib', self.PreviewImageFilename),
                                         wx.BITMAP_TYPE_JPEG)
                self.rawWidth = self.rawImage.GetWidth()
                self.rawHeight = self.rawImage.GetHeight()                
            #print ("Image %s has size %sx%s" % (self.pathname, self.rawWidth, self.rawHeight))
            self.registerMemoryConsumption(self, self.getRawImageMemoryUsage())
            # invalidate bitmap
            self.removeBitmap()
        assert (self.rawImage <> None), ('Raw Image empty in "%s"' % self.getPath())
        return(self.rawImage)


    def releaseMemory(self):
        """Release memory used for self's raw image.
        """
        self.rawImage = None
    


# Setters


# Getters
    def getRawImageMemoryUsage(self):
        """Return self's current memory usage for the raw image, in Bytes.
        """
        if (self.rawImage <> None):
            return(self.rawWidth * self.rawHeight * 3)  # taken from wwx.Image.setData() documentation
        else:
            return(0)


#     def getBitmapMemoryUsage(self):
#         """Return self's current memory usage for the bitmap, in Bytes.
#         """
#         if (self.bitmap <> None):
#             return(self.bitmapWidth * self.bitmapHeight * 3)  # assumption
#         else:
#             return(0)


    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        return('%dx%d' % (self.getRawImage().Width, self.getRawImage().Height))



# Class Initialization
for extension in Image.LegalExtensions: 
    Entry.ProductTrader.registerClassFor(Image, extension)

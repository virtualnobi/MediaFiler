"""
(c) by nobisoft 2015-
"""


# Imports
## standard
import os.path
import gettext
import logging
## contributed
import wx
## nobi
## project
import Installer
from .Entry import Entry
from .Single import Single
import UI  # to access UI.PackagePath



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




# Class 
class Image(Single):
    """A Single representing an image file.
    """



# Constants
    LegalExtensions = ['jpg', 'png', 'gif', 'tif', 'jpeg']
    ConfigurationOptionViewer = 'viewer-image'
    PreviewImageFilename = 'Image.jpg'
    
    

## Inheritance - Entry
    @classmethod
    def getMediaTypeName(cls):
        """Return a translatable name for the subclasses of Single, for filter creation.
        """
        return(_('Image'))

    
    @classmethod
    def getLegalExtensions(cls):
        """Return a set of file extensions which clas can display.
        
        File extensions are lower-case, not including the preceeding dot.
        
        Returns a Set of Strings.
        """
        return(set(cls.LegalExtensions))

    
    @classmethod
    def getConfigurationOptionExternalViewer(cls):
        """Return the configuration option to retrieve the command string for an external viewer of self.
        
        The string must contain the %1 spec which is replaced by the media file name.
        
        Return the external command string, or None if none given.
        """
        return(cls.ConfigurationOptionViewer)



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
#     def runContextMenuItem(self, menuId, parentWindow):
#         """User selected menuId from context menu on self. Execute this function.
#         
#         menuId Number from GUIId function numbers
#         parentWindow wx.Window to open dialogs on
#         Return String to display as status
#             or None
#         """
#         print('Image.runContextMenu: %d on "%s"' % (menuId, self.getPath()))
#         return(super(Image, self).runContextMenuItem(menuId, parentWindow))

    

## Inheritance - Single
    def isIdentical(self, anEntry):
        """Check whether self and anEntry have the same content.
        """
        if (super(Image, self).isIdentical(anEntry)):
            return(self.getRawImage().GetData() == anEntry.getRawImage().GetData())
        else:
            return(False)


    def getRawImage(self):
        """Retrieve raw data (JPG or PNG or GIF) for image.
        """
        if (not self.rawImage):  # lazily load raw image
            #print('Image.getRawImage(%s)' % self.getPath())
            imageType = None
            if ((self.getExtension() == 'jpg')
                or (self.getExtension() == 'jpeg')):
                imageType = wx.BITMAP_TYPE_JPEG
            elif (self.getExtension() == 'png'):
                imageType = wx.BITMAP_TYPE_PNG
            elif (self.getExtension() == 'gif'):
                imageType = wx.BITMAP_TYPE_GIF
            elif (self.getExtension() == 'tif'):
                imageType = wx.BITMAP_TYPE_TIF
            if (imageType):
                self.rawImage = wx.Image(self.getPath(), imageType)
                if (not self.rawImage):
                    logging.debug('Image.getRawImage(): Failed to load "%s"!' % self.getPath())
            else: 
                print('Image.getRawImage(): Illegal type in "%s", using preview image' % self.getPath())
            if (not self.rawImage):
                self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), self.PreviewImageFilename),
                                         wx.BITMAP_TYPE_JPEG)
            assert (self.rawImage <> None), ('Cannot load "%s"' % self.getPath())
            # derive size from raw data
            try:
                self.rawWidth = self.rawImage.GetWidth()
                self.rawHeight = self.rawImage.GetHeight()
            except:
                print('Image: Cannot determine size of "%s", using preview image' % self.getPath())
                self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), self.PreviewImageFilename),
                                         wx.BITMAP_TYPE_JPEG)
                self.rawWidth = self.rawImage.GetWidth()
                self.rawHeight = self.rawImage.GetHeight()                
            #print ("Image %s has size %sx%s" % (self.pathname, self.rawWidth, self.rawHeight))
            self.__class__.registerMemoryConsumption(self, self.getRawImageMemoryUsage())
            # invalidate bitmap
            self.removeBitmap()
        assert (self.rawImage <> None), ('Raw Image empty in "%s"' % self.getPath())
        return(self.rawImage)


    def releaseMemory(self):
        """Release memory used for self's raw image.
        """
        result = self.getRawImageMemoryUsage()
        self.rawImage = None
        return(result)



# Setters


# Getters
    def getRawImageMemoryUsage(self):
        """Return self's current memory usage for the raw image, in Bytes.
        """
        if (self.rawImage <> None):
            return(self.rawWidth * self.rawHeight * 3)  # taken from wx.Image.setData() documentation
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



# Internal - to change without notice
# Class Initialization
for extension in Image.LegalExtensions: 
    Entry.ProductTrader.registerClassFor(Image, extension)

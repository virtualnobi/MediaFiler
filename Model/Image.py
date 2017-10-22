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
# from .Entry import Entry
from .Single import Single
import UI  # to access UI.PackagePath
from Model.CachingController import CachingController



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
    Logger = logging.getLogger(__name__)
    

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
    def __init__(self, model, path):
        """Create an Image from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        super(Image, self).__init__(model, path) 
        # internal state
        self.bitmap = None


## Inheritance - Entry
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
        if (self.rawImage == None):  # lazily load raw image
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
                if (self.rawImage == None):
                    logging.warning('Image.getRawImage(): Failed to load "%s"!' % self.getPath())
            else: 
                logging.warning('Image.getRawImage(): Illegal type in "%s"!' % self.getPath())
            if (self.rawImage == None):
                self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), self.PreviewImageFilename),
                                         wx.BITMAP_TYPE_JPEG)
                assert(self.rawImage <> None), ('Cannot load default image for "%s"!' % self.getPath())
            self.rawImageWidth = self.rawImage.GetWidth()
            self.rawImageHeight = self.rawImage.GetHeight()
            CachingController.allocateMemory(self, 
                                             self.getRawDataMemoryUsage(), 
                                             cachePriority=self.__class__.CachingLevelRawData)
            self.releaseCacheWithPriority(self.__class__.CachingLevelFullsizeBitmap)
            self.releaseCacheWithPriority(self.__class__.CachingLevelThumbnailBitmap)
        return(self.rawImage)



# Setters
# Getters
    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        return('%dx%d' % (self.getRawImageWidth(), self.getRawImageHeight()))



# Internal - to change without notice
# Class Initialization
for extension in Image.LegalExtensions: 
    Installer.getProductTrader().registerClassFor(Image, extension)

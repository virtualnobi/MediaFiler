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



# Package Variables
Logger = logging.getLogger(__name__)



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
    def getRawImageFromPath(cls, aMediaCollection, path):
        """Return a raw image to represent the media content of the given file.
        
        Model.MediaCollection aMediaCollection
        String path
        Return wx.Image or None
        """
        (_, extension) = os.path.splitext(path)
        extension = extension[1:].lower()
        imageType = None
        rawImage = None
        if ((extension == 'jpg')
            or (extension == 'jpeg')):
            imageType = wx.BITMAP_TYPE_JPEG
        elif (extension == 'png'):
            imageType = wx.BITMAP_TYPE_PNG
        elif (extension == 'gif'):
            imageType = wx.BITMAP_TYPE_GIF
        elif (extension == 'tif'):
            imageType = wx.BITMAP_TYPE_TIF
        if (imageType):
            rawImage = wx.Image(path, imageType)
            if (rawImage == None):
                Logger.warning('Image.getRawImageFromPath(): Failed to load "%s"!' % path)
        else: 
            Logger.warning('Image.getRawImageFromPath(): Illegal type in "%s"!' % path)
        return(rawImage)


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
#         smallImage = None
        if (super(Image, self).isIdentical(anEntry)):
            identical = (self.getRawImage().GetData() == anEntry.getRawImage().GetData())
#             if (not identical):  # normalization to small size does not work 
#                 if (not smallImage):
#                     smallImage = self.getRawImage().Rescale(500, 500).GetData()
#                 if (smallImage == anEntry.getRawImage().Rescale(500, 500).GetData()):
#                     Image.Logger.info('Image.isIdentical(): Reduced images identical for\n\t%s\n\t%s' % (self.getPath(), anEntry.getPath()))
#             # TODO: check whether color reduction (or b/w) works 
            return(identical)
        else:
            return(False)


#     def getRawImage(self):
#         """Retrieve raw data (JPG or PNG or GIF) for image.
#         """
#         print('Image.getRawImage(): Deprecated!')
#         if (self.rawImage == None):  # lazily load raw image
#             imageType = None
#             if ((self.getExtension() == 'jpg')
#                 or (self.getExtension() == 'jpeg')):
#                 imageType = wx.BITMAP_TYPE_JPEG
#             elif (self.getExtension() == 'png'):
#                 imageType = wx.BITMAP_TYPE_PNG
#             elif (self.getExtension() == 'gif'):
#                 imageType = wx.BITMAP_TYPE_GIF
#             elif (self.getExtension() == 'tif'):
#                 imageType = wx.BITMAP_TYPE_TIF
#             if (imageType):
#                 self.rawImage = wx.Image(self.getPath(), imageType)
#                 if (self.rawImage == None):
#                     Image.Logger.warning('Image.getRawImage(): Failed to load "%s"!' % self.getPath())
#             else: 
#                 Image.Logger.warning('Image.getRawImage(): Illegal type in "%s"!' % self.getPath())
#             if (self.rawImage == None):
#                 self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), self.PreviewImageFilename),
#                                          wx.BITMAP_TYPE_JPEG)
#                 assert(self.rawImage <> None), ('Cannot load default image for "%s"!' % self.getPath())
#             self.rawImageWidth = self.rawImage.GetWidth()
#             self.rawImageHeight = self.rawImage.GetHeight()
#             CachingController.allocateMemory(self, 
#                                              self.getRawDataMemoryUsage(), 
#                                              cachePriority=self.__class__.CachingLevelRawData)
#             self.releaseCacheWithPriority(self.__class__.CachingLevelFullsizeBitmap)
#             self.releaseCacheWithPriority(self.__class__.CachingLevelThumbnailBitmap)
#         return(self.rawImage)



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


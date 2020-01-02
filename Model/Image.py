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
import pyexiv2
## nobi
## project
import Installer
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
        
        Credits: 
        https://jdhao.github.io/2019/07/31/image_rotation_exif_info/
        https://github.com/LeoHsiao1/pyexiv2#usage
        
        Model.MediaCollection aMediaCollection
        String path
        Return wx.Image or None
        """
        (_, extension) = os.path.splitext(path)
        extension = extension[1:].lower()
        imageType = None
        rawImage = None
        orientation = 1  # EXIF orientation as-is
        rotation = 'N'  # N: normal, L: left, R:right, M: mirror
        if ((extension == 'jpg')
            or (extension == 'jpeg')):
            imageType = wx.BITMAP_TYPE_JPEG
            try:  # to determine orientation from EXIF metadata in path
                Logger.debug('Image.getRawImageFromPath(): Reading metadata from "%s"' % path)
                image = pyexiv2.Image(path)
                metadata = image.read_exif()  # {'Exif.Image.DateTime': '2019:06:23 19:45:17', 'Exif.Image.Artist': 'TEST', ...}
                Logger.debug('Image.getRawImageFromPath(): Read metadata %s' % metadata)
                orientation = int(metadata['Exif.Image.Orientation'])
                Logger.debug('Image.getRawImageFromPath(): EXIF orientation is %s' % orientation)
            except:  # failed, assume as-is
                Logger.debug('Image.getRawImageFromPath(): No EXIF orientation information, assuming as-is')
                orientation = 1
            if (orientation == 6):  # clockwise 90 degrees
                rotation = 'R'
            elif (orientation == 8):  # clockwise 270 degrees
                rotation = 'L'
            elif (orientation == 3):  # clockwise 180 degrees
                rotation = 'M'
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
                rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), Image.PreviewImageFilename),
                                    wx.BITMAP_TYPE_JPEG)
            if (rotation != 'N'):
                Logger.debug('Image.getRawImageFromPath(): Rotating %s degrees' % rotation)
                #centerPoint = (rawImage.GetWidth()/2, rawImage.GetHeight()/2)
                #rawImage = rawImage.Rotate(rotation, centerPoint, interpolating=True)
                if (rotation == 'R'):
                    rawImage = rawImage.Rotate90(True)
                elif (rotation == 'L'):
                    pass # rawImage = rawImage.Rotate90(False)
                else:  # must be 'M'
                    rawImage = rawImage.Rotate180()
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
    def isIdenticalContent(self, anEntry):
        """Check whether self and anEntry have the same content.
        """
        if (super(Image, self).isIdenticalContent(anEntry)):
            identical = (self.getRawImage().GetData() == anEntry.getRawImage().GetData())
            return(identical)
        else:
            return(False)



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


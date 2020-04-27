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
from Model import Installer
from Model.Single import Single
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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
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
    def getMetadataFromPath(cls, path):
        """Return metadata from the given file, if it exists.

        Credits:
        https://github.com/LeoHsiao1/pyexiv2#usage
        
        Return dict (empty if no metadata available)
        """
        try:
            Logger.debug('Image.getMetadataFromPath(): Reading metadata from "%s"' % path)
            image = pyexiv2.Image(path)
            result = image.read_exif()  # {'Exif.Image.DateTime': '2019:06:23 19:45:17', 'Exif.Image.Artist': 'TEST', ...}
            Logger.debug('Image.getMetadataFromPath(): Metadata is %s' % result)
        except:
            Logger.debug('Image.getMetadataFromPath(): No metadata found')
            result = {}
        return(result)


    @classmethod
    def getRotationFromMetadata(cls, metadata):
        """Return rotation applied to original (file) image.
                
        Must be a class method to be useful during import.
        
        dict metadata contains JPG/EXIF metadata
        Returns 'N' = normal, no rotation
                'R' = right
                'L' = left
                'M' = mirror, upside
        """
        orientation = 1
        rotation = 'N'  # N: normal, L: left, R: right, M: mirror
        try:
            orientation = int(metadata['Exif.Image.Orientation'])
            Logger.debug('Image.getRotationFromMetadata(): EXIF orientation is %s' % orientation)
        except:  # failed, assume as-is
            Logger.debug('Image.getRotationFromMetadata(): No EXIF orientation information, assuming as-is')
        if (orientation == 6):  # clockwise 90 degrees
            rotation = 'R'
        elif (orientation == 8):  # clockwise 270 degrees
            rotation = 'L'
        elif (orientation == 3):  # clockwise 180 degrees
            rotation = 'M'
        return(rotation)

    
    @classmethod
    def getRawImageFromPath(cls, aMediaCollection, path):
        """Return a raw image to represent the media content of the given file.
                
        Must be a class method to be useful during import.
        
        Credits for JPG/EXIF rotation: 
        https://jdhao.github.io/2019/07/31/image_rotation_exif_info/
        
        Model.MediaCollection aMediaCollection
        String path
        Return wx.Image or None
        """
        (_, extension) = os.path.splitext(path)
        extension = extension[1:].lower()
        imageType = None
        rawImage = None
        rotation = 'N'  # N: normal, L: left, R: right, M: mirror
        if ((extension == 'jpg')
            or (extension == 'jpeg')):
            imageType = wx.BITMAP_TYPE_JPEG
            metadata = cls.getMetadataFromPath(path)
            rotation = cls.getRotationFromMetadata(metadata)
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
                rotation = 'N'
            if (rotation != 'N'):
                Logger.debug('Image.getRawImageFromPath(): Rotating %s' % rotation)
                if (rotation == 'R'):
                    rawImage = rawImage.Rotate90(True)
                elif (rotation == 'L'):
                    rawImage = rawImage.Rotate90(False)
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
        self.metadataExif = None
        self.rotation = None
        self.bitmap = None



## Inheritance - Entry
## Inheritance - Single
    def isIdenticalContent(self, anEntry):
        """Check whether self and anEntry have the same content.
        """
        if (super(Image, self).isIdenticalContent(anEntry)):
#             identical = (self.getRawImage().GetData() == anEntry.getRawImage().GetData())
            identical = (self.getRawImage() == anEntry.getRawImage())  # wxPython 4 TODO: Is this checking for bitwise equality?
            return(identical)
        else:
            return(False)



# Setters
# Getters
    def getIdentifier(self):
        """override Entry.getIdentifier()
        
        Add a rotation indicator to the identifier
        """
        result = super(Image, self).getIdentifier()
        if (self.rotation 
            and (self.rotation != 'N')):
            result = ('%s (%s)' % (result, self.rotation))
        return(result)


    def getRawImage(self):
        """override Single.getRawImage()
        
        If image needs to be loaded, make sure the rotation indicator is added to self's name in tree.
        """
        Logger.debug('Image.getRawImage(%s)' % self)
        if (self.getOrganizer().getNumber() == 81):
            pass
        if (self.rawImage):
            return(self.rawImage)
        result = super(Image, self).getRawImage()
        self.rotation = self.__class__.getRotationFromMetadata(self.getMetadata())
        if (self.rotation
            and (self.rotation != 'N')):
            self.changedAspect('name') 
        return(result)


    def getMetadata(self):
        """Return image metadata, depending on image file type.
        
        Supported so far: 
        - JPG/EXIF
        
        Return dict (empty if no metadata available)
        """
        if ((self.getExtension() == 'jpg')
            or (self.getExtension() == 'jpeg')):
            if (self.metadataExif == None):
                self.metadataExif = self.__class__.getMetadataFromPath(self.getPath())
            return(self.metadataExif)
        return({})
        

    def getResolution(self):
        """overwrite Single.getResolution()
        """
        result = None
        md = self.getMetadata()
        if ('Exif.Photo.PixelXDimension' in md): 
            result = int(md['Exif.Photo.PixelXDimension']) * int(md['Exif.Photo.PixelYDimension'])
        else:
            result = Single.getResolution(self)
        return result


#     def getSizeString(self):
#         """Return a String describing the size of self.
#         
#         Return a String
#         """
#         return('%dx%d' % (self.getRawImageWidth(), self.getRawImageHeight()))



# Internal - to change without notice
# Class Initialization
for extension in Image.LegalExtensions: 
    Installer.getProductTrader().registerClassFor(Image, extension)


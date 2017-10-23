"""
(c) by nobisoft 2015-
"""


# Imports
## standard
import datetime
import re
import os.path
import gettext
import subprocess
import logging
import cStringIO
## contributed
import wx
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




# Class 
class Movie(Single):
    """A Single representing a movie file.
    """



# Constants
    LegalExtensions = ['mov', 'mp4', '3gp', 'mpg', 'avi', 'wmv', 'vob']  # all file formats handled by Movie
    ConfigurationOptionViewer = 'viewer-movie'
    ConfigurationOptionFfmpeg = 'ffmpeg'
    CaptureFramePosition = 0.1  # percentage of movie duration to take capture as placeholder
    PreviewImageFilename = 'Movie.jpg'  # image shown as placeholder for movie if ffmpeg doesn't work



# Class Methods
    @classmethod
    def getMediaTypeName(cls):
        """Return a translatable name for the subclasses of Single, for filter creation.
        """
        return(_('Movie'))

    
    @classmethod
    def getLegalExtensions(cls):
        """Return a set of file extensions which cls can display.
        
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
        """Create a Movie from the file at PATH, based on MediaCollection MODEL. 
        """
        # inheritance
        Single.__init__(self, model, path)
        # internal state
        self.duration = None
        return(None)



## Inheritance - Entry
#     def runContextMenuItem(self, menuId, parentWindow):
#         """User selected menuId from context menu on self. Execute this function.
#         
#         menuId Number from GUIId function numbers
#         parentWindow wx.Window to open dialogs on
#         Returns
#         """
#         print('Running function %d on "%s"' % (menuId, self.getPath()))
#         return(super(Movie, self).runContextMenuItem(menuId, parentWindow))



## Inheritance - Single
    def getRawImage(self):
        """Retrieve raw data (JPG or PNG or GIF) for image.
        """
        if (self.rawImage <> None):
            return(self.rawImage)
        ffmpeg = self.model.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpeg):
            try:
                logging.debug('Movie.getRawImage(): Using "%s"' % ffmpeg)                
#                 proc = subprocess.Popen([ffmpeg, "-i", self.getPath()], stderr=subprocess.PIPE)
#                 (dummy, result) = proc.communicate()
#                 m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", result)
#                 if (m == None):
#                     target = '5'
#                     logging.warning('Movie.getRawImage(): Cannot determine duration, using %s secs as offset for "%s"' % (target, self.getPath()))
#                 else:
#                     # Avoiding strptime here because it has some issues handling milliseconds.
#                     m = [int(m.group(i)) for i in range(1, 5)]
#                     duration = datetime.timedelta(hours=m[0],
#                                                   minutes=m[1],
#                                                   seconds=m[2],
#                                                   # * 10 because truncated to 2 decimal places
#                                                   milliseconds=m[3] * 10
#                                                   ).total_seconds()
                duration = self.getDuration()
                if (duration):
                    target = max(0, min(duration * self.__class__.CaptureFramePosition, duration - 0.1))
                else:
                    target = 5 
                    logging.warning('Movie.getRawImage(): Cannot determine duration, using %s secs as offset for "%s"' % (target, self.getPath()))
                targetString = "{:.3f}".format(target)
                logging.debug('Movie.getRawImage(): Duration is %s, target frame is %s' % (duration, target))            
                args = [ffmpeg,
                        "-ss", targetString,
                        "-i", self.getPath(),
                        "-map", "v:0",     # first video stream
                        "-frames:v", "1",  # 1 frame
                        "-f", "mjpeg",     # motion jpeg (aka. jpeg since 1 frame) output
                        "pipe:"            # pipe output to stdout
                        ]
                proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (output, _) = proc.communicate()
                if (proc.returncode):
                    raise subprocess.CalledProcessError(proc.returncode, args)
                if (not output):
                    raise subprocess.CalledProcessError(-2, args)
                stream = cStringIO.StringIO(output)
                self.rawImage = wx.ImageFromStream(stream)
            except Exception as e:
                logging.error('Movie.getRawImage(): Cannot retrieve frame from "%s"; error follows:\n%s' % (self.getPath(), e))
        if (self.rawImage == None):
            self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), Movie.PreviewImageFilename),
                                     wx.BITMAP_TYPE_JPEG)
            assert (self.rawImage <> None), ('Cannot load default image for "%s"' % self.getPath())
        self.rawImageWidth = self.rawImage.GetWidth()
        self.rawImageHeight = self.rawImage.GetHeight()
        return(self.rawImage)



# Setters
# Getters
    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        duration = self.getDuration()
        if (duration <> None):
            return(_('%d secs') % duration)
        else:
            return(_('unknown duration'))



# Event Handlers
# Internal - to change without notice
    def getDuration(self):
        """Determine the duration of the movie, in seconds
        
        Return Number
        """
        if (self.duration <> None):
            return(self.duration)
        ffmpeg = self.model.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpeg):
            try:
                args = [ffmpeg, 
                        '-i',
                        self.getPath()]
                logging.debug('Movie.getDuration(): Calling "%s"' % args)
                proc = subprocess.Popen(args, stderr=subprocess.PIPE)
                (_, result) = proc.communicate()
                m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', result)
                if (m == None):
                    logging.warning('Movie.getDuration(): Cannot determine duration for "%s"!' % self.getPath())
                else:
                    # Avoiding strptime here because it has some issues handling milliseconds.
                    m = [int(m.group(i)) for i in range(1, 5)]
                    self.duration = datetime.timedelta(hours=m[0],
                                                       minutes=m[1],
                                                       seconds=m[2],
                                                       # * 10 because truncated to 2 decimal places
                                                       milliseconds=m[3] * 10
                                                       ).total_seconds()
            except Exception as e:
                logging.warning('Movie.getDuration(): Cannot determine duration due to error:\n%s' % e)
        else:
            logging.warning('Movie.getDuration(): No ffmpeg specified with %s' % Movie.ConfigurationOptionFfmpeg)
        return(self.duration)



# Class Initialization
for extension in Movie.LegalExtensions: 
    Installer.getProductTrader().registerClassFor(Movie, extension)  # register Movie to handle extension




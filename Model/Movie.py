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
import nobi.win_subprocess  # @UnusedImport - this broken subprocess.popen() to handle unicode 
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



# Package Variables
Logger = logging.getLogger(__name__)



# Class 
class Movie(Single):
    """A Single representing a movie file.
    """



# Constants
    LegalExtensions = ['mov', 'mp4', '3gp', 'mpg', 'avi', 'wmv', 'vob']  # all file formats handled by Movie
    ConfigurationOptionViewer = 'viewer-movie'
    ConfigurationOptionFfmpeg = 'ffmpeg'
    CaptureFramePosition = 0.1  # percentage of movie duration to take capture as placeholder
    PreviewImageFilename = 'Movie.jpg'  # image shown as placeholder for movie if no capture can be taken



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
    def getDurationFromPath(self, aMediaCollection, path):
        """Determine the duration of the given movie, in seconds.
        
        Model.MediaCollection aMediaCollection
        String path
        Return Number or None
        """
        self.duration = None
        ffmpeg = aMediaCollection.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpeg):
            try:
                args = [ffmpeg,
                        u'-i',
                        path]
                Logger.debug('Movie.getDurationFromPath(): Calling "%s"' % args)
                proc = subprocess.Popen(args, stderr=subprocess.PIPE)
                (_, result) = proc.communicate()
                m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', result)
                if (m == None):
                    Logger.warning('Movie.getDurationFromPath(): Cannot determine duration for "%s"!' % path)
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
                Logger.warning('Movie.getDurationFromPath(): Cannot determine duration due to error:\n%s' % e)
        else:
            Logger.warning('Movie.getDurationFromPath(): No ffmpeg specified with option "%s"' % Movie.ConfigurationOptionFfmpeg)
        return(self.duration)


    @classmethod
    def getRawImageFromPath(cls, aMediaCollection, path):
        """Return a raw image to represent the media content of the given file.
        
        Model.MediaCollection aMediaCollection
        String path 
        Return wx.Image or None
        """
        rawImage = None
        ffmpeg = aMediaCollection.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpeg):
            try:
                Logger.debug('Movie.getRawImageFromPath(): Using "%s"' % ffmpeg)                
                duration = cls.getDurationFromPath(aMediaCollection, path)
                if (duration):
                    target = max(0, min(duration * Movie.CaptureFramePosition, duration - 0.1))
                else:
                    target = 5 
                    logging.warning('Movie.getRawImageFromPath(): Cannot determine duration, using %s secs as offset for "%s"' % (target, path))
                targetString = "{:.3f}".format(target)
                logging.debug('Movie.getRawImageFromPath(): Duration is %s, target frame is %s' % (duration, target))            
                args = [ffmpeg,
                        "-ss", targetString,
                        "-i", path,
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
                rawImage = wx.ImageFromStream(stream)
            except Exception as e:
                Logger.error('Movie.getRawImageFromPath(): Cannot retrieve frame from "%s" due to error:\n%s' % (path, e))
        else:
            Logger.warning('Movie.getRawImageFromPath(): No ffmpeg specified with option "%s"' % Movie.ConfigurationOptionFfmpeg)
        if (rawImage == None):
            rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), Movie.PreviewImageFilename),
                                wx.BITMAP_TYPE_JPEG)
            if (rawImage == None):
                Logger.error('Movie.getRawImageFromPath(): Cannot load default movie image for "%s"' % path)
                raise Exception
        return(rawImage)


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



# Setters
# Getters
    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        seconds = self.getDuration()
        if (seconds <> None):
            minutes = int(seconds / 60)
            seconds = int(seconds % 60)
            fmt = _('%d secs')
            numberList = (seconds, )
            if (0 < minutes):
                fmt = (_('%d mins, ') + fmt)
                numberList = (minutes, seconds)
            return(fmt % numberList)
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

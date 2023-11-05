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
#from io import StringIO
from io import BytesIO
## contributed
# import nobi.win_subprocess  # @UnusedImport - this broken subprocess.popen() to handle unicode 
import wx
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
    def getMetadataFromPath(cls, aMediaCollection, path):
        """Return metadata from the given file, if it exists.

        MediaCollection
        String path
        Return dict (empty if no metadata available)
        """
        result = {}
        ffmpegCmd = aMediaCollection.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpegCmd):
            try:
                args = [ffmpegCmd, u'-i', path]
                Logger.debug('Movie.getMetadataFromPath(): Calling "%s"' % args)
                output = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
                for line in output.split('\n'):
                    Logger.debug('Movie.getMetadataFromPath(): Processing ffmpeg output "%s"' % line)
                    match = re.search(r'    (\S+)\s*: (.+)', line)
                    if (match):
                        if (match.group(1) == 'creation_time'):  # time given as 2014-05-20T14:13:43.000000Z
                            timestamp = re.search(r'(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d)', match.group(2))
                            if (timestamp):
                                Logger.debug('Movie.getMetadataFromPath(): Found creation time "%s"' % match.group(2))
                                result['year'] = timestamp.group(1)
                                result['month'] = timestamp.group(2)
                                result['day'] = timestamp.group(3)
                                result['hour'] = timestamp.group(4)
                                result['minute'] = timestamp.group(5)
                            else:
                                Logger.debug('Movie.getMetadataFromPath(): Found un-interpretable creation time "%s"' % match.group(1))
                                result[match.group(1)] = match.group(2)
                        else:
                            Logger.debug('Movie.getMetadataFromPath(): Found metadata %s = %s' % (match.group(1), match.group(2)))
                            result[match.group(1)] = match.group(2)
                    else:
                        match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', line)
                        if (match):
                            # Avoiding strptime() here because it has some issues handling milliseconds.
                            duration = [int(match.group(i)) for i in range(1, 5)]
                            result['seconds'] = datetime.timedelta(hours=duration[0],
                                                                   minutes=duration[1],
                                                                   seconds=duration[2],
                                                                   milliseconds=duration[3] * 10  # * 10 because truncated to 2 decimal places
                                                                   ).total_seconds()
                            Logger.debug('Movie.getMetadataFromPath(): Found duration "%s" = %dsecs' % (duration, result['seconds']))
                        else:
                            match = re.search(r'Stream.*Video.*, (\d?\d?\d\d\d)x(\d?\d?\d\d\d)', line)
                            if (match):
                                result['width'] = match.group(1)
                                result['height'] = match.group(2)
                                Logger.debug('Movie.getMetadataFromPath(): Found resolution %sx%s' % (result['width'], result['height']))
            except Exception as e:
                Logger.warning('Movie.getMetadataFromPath(): Cannot read metadata due to error:\n%s' % e)
        else:
            Logger.warning('Movie.getMetadataFromPath(): No ffmpeg specified with option "%s"' % Movie.ConfigurationOptionFfmpeg)
        return(result)

    
    @classmethod
    def getDurationFromPath(self, aMediaCollection, path):
        """Determine the duration of the given movie, in seconds.

        TODO: Remove if metadataFfmpeg is available
        
        Model.MediaCollection aMediaCollection
        String path
        Return Number or None
        """
        self.duration = None
        ffmpeg = aMediaCollection.getConfiguration(Movie.ConfigurationOptionFfmpeg)
        if (ffmpeg):
            try:
                args = [ffmpeg, u'-i', path]
                Logger.debug('Movie.getDurationFromPath(): Calling "%s"' % args)
                output = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
                m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', output)
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
            Logger.warning('Movie.getDurationFromPath(): No ffmpeg specified with setting "%s"' % Movie.ConfigurationOptionFfmpeg)
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
#                 proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#                 (output, _) = proc.communicate()
#                 if (proc.returncode):
#                     raise subprocess.CalledProcessError(proc.returncode, args)
                cp = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # Python 3
                if (cp.returncode):
                    raise subprocess.CalledProcessError(cp.returncode, args)
                if (not cp.stdout):
                    raise subprocess.CalledProcessError(-2, args)
                stream = BytesIO(cp.stdout)
#                 rawImage = wx.ImageFromStream(stream, type=wx.BITMAP_TYPE_JPEG)
                rawImage = wx.Image(stream, type=wx.BITMAP_TYPE_JPEG)  # wxPython 4
            except Exception as e:
                Logger.error('Movie.getRawImageFromPath(): Cannot retrieve frame from "%s" due to error:\n%s' % (path, e))
                rawImage = None
        else:
            Logger.warning('Movie.getRawImageFromPath(): No ffmpeg specified with option "%s"' % Movie.ConfigurationOptionFfmpeg)
            rawImage = None
        if (rawImage == None):
            try:
                rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), Movie.PreviewImageFilename),
                                    wx.BITMAP_TYPE_JPEG)
            except Exception as exc:
                Logger.error('Movie.getRawImageFromPath(): Cannot load default movie image due to\n%s' % exc)
                rawImage = None
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
        self.metadataFfmpeg = None
        self.duration = None



# Setters
# Getters
    def getMetadata(self):
        """Return video metadata.
        
        Return dict (empty if no metadata available)
        """
        if (self.metadataFfmpeg == None):
            self.metadataFfmpeg = Movie.getMetadataFromPath(self.model, self.getPath())
        return(self.metadataFfmpeg)


    def getSizeString(self):
        """overwrite Single.getSizeString()
        
        Add duration to the resolution.
        """
        resolution = super(Movie, self).getSizeString()
        seconds = self.getDuration()
        if (seconds != None):
            minutes = int(seconds / 60)
            seconds = int(seconds % 60)
            fmt = _('%d secs')
            numberList = (seconds, )
            if (0 < minutes):
                fmt = (_('%d mins, ') + fmt)
                numberList = (minutes, seconds)
            duration = (fmt % numberList)
        else:
            duration = _('unknown duration')
        return(resolution + ', ' + duration)



# Event Handlers
# Internal - to change without notice
    def getDuration(self):
        """Determine the duration of the movie, in seconds
        
        Return Number
        """
        if (self.duration != None):
            return self.duration
        md = self.getMetadata()
        self.duration = (md['seconds'] if 'seconds' in md else -1)
#         ffmpeg = self.model.getConfiguration(Movie.ConfigurationOptionFfmpeg)
#         if (ffmpeg):
#             try:
#                 args = [ffmpeg, 
#                         '-i',
#                         self.getPath()]
#                 logging.debug('Movie.getDuration(): Calling "%s"' % args)
# #                 proc = subprocess.Popen(args, stderr=subprocess.PIPE)
# #                 (_, result) = proc.communicate()
#                 output = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout  # Python 3
#                 m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', output)
#                 if (m == None):
#                     logging.warning('Movie.getDuration(): Cannot determine duration for "%s"!' % self.getPath())
#                 else:
#                     # Avoiding strptime here because it has some issues handling milliseconds.
#                     m = [int(m.group(i)) for i in range(1, 5)]
#                     self.duration = datetime.timedelta(hours=m[0],
#                                                        minutes=m[1],
#                                                        seconds=m[2],
#                                                        # * 10 because truncated to 2 decimal places
#                                                        milliseconds=m[3] * 10
#                                                        ).total_seconds()
#             except Exception as e:
#                 logging.warning('Movie.getDuration(): Cannot determine duration due to error:\n%s' % e)
#         else:
#             logging.warning('Movie.getDuration(): No ffmpeg specified with %s' % Movie.ConfigurationOptionFfmpeg)
        return self.duration 



# Class Initialization
for extension in Movie.LegalExtensions: 
    Installer.getProductTrader().registerClassFor(Movie, extension)  # register Movie to handle extension

"""
(c) by nobisoft 2015-
"""


# Imports
## standard
import os.path
import gettext
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
class Movie(Single):
    """A Single representing a movie file.
    """



# Constants
    LegalExtensions = ['mov', 'mp4', '3gp', 'mpg']  # all file formats handled by Movie
    ConfigurationOptionViewer = 'viewer-movie'
    PreviewImageFilename = 'Movie.jpg'  # image shown as placeholder for movie



# Class Methods
    @classmethod
    def getMediaTypeName(cls):
        """Return a translatable name for the subclasses of Single, for filter creation.
        """
        return(_('Movie'))

    
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
        """Create a Movie from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        Single.__init__(self, model, path)
        # internal state
        self.rawImage = wx.Image(os.path.join(Installer.getLibraryPath(), Movie.PreviewImageFilename),
                                 wx.BITMAP_TYPE_JPEG)
        return(None)



## Inheritance - Entry
    def runContextMenuItem(self, menuId, parentWindow):
        """User selected menuId from context menu on self. Execute this function.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Returns
        """
        print('Running function %d on "%s"' % (menuId, self.getPath()))
        return(super(Movie, self).runContextMenuItem(menuId, parentWindow))



## Inheritance - Single
    def releaseMemory(self):
        """
        """
        return(0)  # TODO: if using a frame of the video, it must be freed


    def getRawImage (self):
        """Retrieve raw data (JPG or PNG or GIF) for image.

        TODO: Extract first frame of movie to display
        
        See https://tobilehman.com/blog/2013/01/20/extract-array-of-frames-from-mp4-using-python-opencv-bindings/
        or https://stackoverflow.com/questions/10672578/extract-video-frames-in-python
        """
        return(self.rawImage)


    def getBitmap (self, width, height):
        """Retrieve preview image as bitmap, resizing it to fit into given size.
        """
        return(self.getRawImage().Copy().Rescale(width, height).ConvertToBitmap())



# Setters
# Getters
# Event Handlers
# Internal - to change without notice
# Class Initialization
for extension in Movie.LegalExtensions: 
    Entry.ProductTrader.registerClassFor(Movie, extension)  # register Movie to handle extension




# script using ffmpeg to extract middle frame of video
# !/usr/bin/env python
# 
# # Any copyright is dedicated to the Public Domain.
# # http://creativecommons.org/publicdomain/zero/1.0/
# # Written in 2013 - Nils Maier
# 
# import datetime
# import os
# import re
# import subprocess
# import sys
# 
# 
# def which(program):
#     """ Somewhat equivalent to which(1) """
# 
#     def is_executable(fpath):
#         return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
# 
#     if is_executable(program):
#         return program
#     path, program = os.path.split(program)
#     if path:
#         return None
#     for path in os.environ["PATH"].split(os.pathsep):
#         path = path.strip('"')
#         exe = os.path.join(path, program)
#         if is_executable(exe):
#             return exe
#         # Windows-style
#         exe = os.path.join(path, "{}.exe".format(program))
#         if is_executable(exe):
#             return exe
#     return None
# 
# 
# def thumb_with_ffmpeg(infile, position=0.5, executable=None):
#     """
#     Extract a thumbnail using ffmpeg
# 
#     :param infile: File to thumbnail.
#     :param position: Position at which to take the thumbnail. Default: 0.5
#     :param executable: Executable to use. Default: first "ffmpeg" in $PATH
#     :returns: The thumbnail data (binary string)
#     """
# 
#     ffmpeg = which(executable or "ffmpeg")
#     if not ffmpeg:
#         raise RuntimeError(
#             "Failed to find ffmpeg executable: {}".format(executable))
#     if position < 0 or position >= 1.0:
#         raise ValueError(
#             "Position {} is not between 0.0 and 1.0".format(position))
# 
#     proc = subprocess.Popen([ffmpeg, "-i", infile], stderr=subprocess.PIPE)
#     _, result = proc.communicate()
#     m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", result)
#     if not m:
#         raise KeyError("Cannot determine duration")
#     # Avoiding strptime here because it has some issues handling milliseconds.
#     m = [int(m.group(i)) for i in range(1, 5)]
#     duration = datetime.timedelta(hours=m[0],
#                                   minutes=m[1],
#                                   seconds=m[2],
#                                   # * 10 because truncated to 2 decimal places
#                                   milliseconds=m[3] * 10
#                                   ).total_seconds()
#     target = max(0, min(duration * position, duration - 0.1))
#     target = "{:.3f}".format(target)
#     args = [ffmpeg,
#             "-ss", target,
#             "-i", infile,
#             "-map", "v:0",     # first video stream
#             "-frames:v", "1",  # 1 frame
#             "-f", "mjpeg",     # motion jpeg (aka. jpeg since 1 frame) output
#             "pipe:"            # pipe output to stdout
#             ]
#     proc = subprocess.Popen(args, stdout=subprocess.PIPE,
#                             stderr=subprocess.PIPE)
#     output, _ = proc.communicate()
#     if proc.returncode:
#         raise subprocess.CalledProcessError(proc.returncode, args)
#     if not output:
#         raise subprocess.CalledProcessError(-2, args)
#     return output
# 
# 
# if __name__ == "__main__":
#     from argparse import ArgumentParser, ArgumentTypeError
# 
#     def percentage(x):
#         x = float(x)
#         if x < 0.0 or x >= 1.0:
#             raise ArgumentTypeError(
#                 "{} not in percentage range [0.0, 1.0)".format(x))
#         return x
# 
#     parser = ArgumentParser(
#         description="Extract a thumbnail from a media file using ffmpeg")
#     parser.add_argument("infile", type=str, help="Input file")
#     parser.add_argument("outfile", type=str, help="Output file")
#     parser.add_argument("-f", "--ffmpeg", type=str, default=None,
#                         help="use this ffmpeg binary, "
#                              "default: check $PATH for ffmpeg")
#     parser.add_argument("-p", "--position", type=percentage, default=0.5,
#                         help="thumbnail at this position (percentage), "
#                              "default: 0.5")
#     args = parser.parse_args()
# 
#     try:
#         output = thumb_with_ffmpeg(args.infile, args.position, args.ffmpeg)
#         with open(args.outfile, "wb") as op:
#             op.write(output)
#     except Exception as ex:
#         print >>sys.stderr, "Error:", ex
#         sys.exit(ex.returncode or 1)
#         
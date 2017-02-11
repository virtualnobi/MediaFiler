"""
(c) by nobisoft 2015-
"""


# Imports
## standard
import os.path
import subprocess
## contributed
import wx
## nobi
## project
from UI import GUIId
from .Entry import Entry
from .Single import Single



# Class 
class Movie(Single):
    """A Single representing a movie file.
    """



# Constants
    LegalExtensions = ['mov', 'mp4', '3gp']  # all file formats handled by Movie
    PreviewImageFilename = 'Movie.jpg'  # image shown as placeholder for movie



# Lifecycle
    def __init__ (self, model, path):
        """Create a Movie from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        Single.__init__(self, model, path)
        # internal state
        # load preview image for movies
        self.rawImage = wx.Image(os.path.join (self.model.rootDirectory, '..', 'lib', Movie.PreviewImageFilename), 
                                 wx.BITMAP_TYPE_JPEG)        
        return(None)



## Inheritance - Entry
    @classmethod
    def getLegalExtensions(clas):
        """Return a set of file extensions which clas can display.
        
        File extensions are lower-case, not including the preceeding dot.
        
        Returns a Set of Strings.
        """
        return(set(clas.LegalExtensions))

    
    def runContextMenuItem(self, menuId, parentWindow):
        """User selected menuId from context menu on self. Execute this function.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Returns
        """
        print('Running function %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.StartExternalViewer):
            subprocess.call(['vlc.exe', self.getPath()], shell=True)
        else:
            return(super(Movie, self).runContextMenuItem(menuId, parentWindow))



## Inheritance - Single
    def releaseMemory(self):
        """
        """
        pass


    def getRawImage (self):
        """Retrieve raw data (JPG or PNG or GIF) for image.
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

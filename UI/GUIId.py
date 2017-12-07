# -*- coding: UTF-8 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## standard
import os.path
import gettext
## contributed
import wx
## nobi
## project
import UI  # to access UI.PackagePath



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at %s; using originals instead of %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message



# Constant Strings
AppTitle = 'MediaFiler'
MessageDuplicatesDeleted = _('%d duplicate media deleted')
TextGroupSizeString = _('%d media')



# Sizes and Ranges
MaxNumberRecentFiles = 10  # maximum number of stored recent root directories
MaxNumberScenes = 99  # maximum number of change scene functions
MaxNumberPerspectives = 10  # maximum number of stored perspectives
MaxNumberMoveToLocations = 10  # max number of remembered last move-to locations



# Status Bar components
SB_Info = 0  # informational messages
SB_Root = 1  # root directory
SB_Organization = 2  # organization of images: by date or by name
SB_Filter = 3  # number if filters active



# Identifiers and texts to register event handlers
FunctionNames = {}  # mapping event identifiers to texts
def generateWxIdForLabel(label):
    idx = wx.NewId()
    FunctionNames[idx] = label
    return(idx)



## File
LoadRecentDirectory = wx.NewId()  # load first recent root directory
for i in xrange(MaxNumberRecentFiles - 1):  # reserve additional menu items for more recent directories
    wx.NewId()
ChangeRootDirectory = generateWxIdForLabel(_('Change Media Directory'))
ReloadDirectory = generateWxIdForLabel(_('Reload Media'))
ExportImages = generateWxIdForLabel(_('Export (Filtered) Media'))
FunctionNames[wx.ID_EXIT] = _('Exit')

## Image
EntryFunctionFirst = wx.NewId()  # allow forwarding of range of menu events to MediaFiler.Entry in MediaCanvas and MediaTreeCtrl
DeleteImage = generateWxIdForLabel(_('Delete Media "%s"'))
DeleteDoubles = generateWxIdForLabel(_('Delete Doubles'))

RemoveNew = generateWxIdForLabel(_('Remove Import Indicator'))
RandomName = generateWxIdForLabel(_('Choose Random Name'))
ChooseName = generateWxIdForLabel(_('Choose Name Manually...'))
ConvertToGroup = generateWxIdForLabel(_('Convert to Group'))  # convert a Single into a Group
ConvertToSingle = generateWxIdForLabel(_('Convert to Single'))  # convert a Single into a Group
RemoveIllegalElements = generateWxIdForLabel(_('Remove Illegal Tags'))

FilterIdentical = generateWxIdForLabel(_('Filter Identical'))
FilterSimilar = generateWxIdForLabel(_('Filter Similar'))

StartExternalViewer = generateWxIdForLabel(_('View in External Program'))
SendMail = generateWxIdForLabel(_('Send Email'))
# Functions specific to OrganizationByName
SelectScene = generateWxIdForLabel(_('Move to scene...'))  # TODO: merge with SelectMoveTo
for i in xrange(MaxNumberScenes - 1):  # reserve additional menu items for more scene numbers
    wx.NewId()
RelabelScene = generateWxIdForLabel(_('Rename scene to...'))
# Functions Specific to OrganizationByDate
SelectMoveTo = generateWxIdForLabel(_('Move to...'))
for i in xrange(MaxNumberMoveToLocations - 1):
    wx.NewId()
EntryFunctionLast = wx.NewId()  # allow forwarding of range of menu events to MediaFiler.Entry in MediaCanvas and MediaTreeCtrl

## View
ToggleFilterPane = generateWxIdForLabel(_('Toggle Filter Pane'))
ToggleFilter = generateWxIdForLabel(_('Toggle Filter'))
ApplyFilter = generateWxIdForLabel(_('Apply Filter'))
ClearFilter = generateWxIdForLabel(_('Clear Filter'))
ToggleTreePane = generateWxIdForLabel(_('Toggle Tree Pane'))
ToggleClassificationPane = generateWxIdForLabel(_('Toggle Classification Pane'))
ToggleLogPane = generateWxIdForLabel(_('Toggle Log Pane'))
PreviousImage = generateWxIdForLabel(_('Previous Media'))
NextImage = generateWxIdForLabel(_('Next Media'))
StopSlideshow = generateWxIdForLabel(_('Stop Slideshow'))
ResumeSlideshow = generateWxIdForLabel(_('Resume Slideshow'))
QuickSlideshow = generateWxIdForLabel(_('Present Quickly'))
SlowSlideshow = generateWxIdForLabel(_('Present Slowly'))

## Perspectives
#-FirstPerspective = wx.ID_HIGHEST + PerspectiveFirstStart  # load first perspective, subsequent codes used by other perspectives
LoadPerspective = wx.NewId()  # load first perspective
for i in xrange(MaxNumberPerspectives - 1):  # reserve additional menu idemts for more perspectives
    wx.NewId()
CreatePerspective = wx.NewId ()  # create perspective
DeletePerspective = wx.NewId ()  # delete perspective

## Import
TestImport = generateWxIdForLabel(_('Test Import'))
Import = generateWxIdForLabel(_('Import'))

## Tools
GenerateLinkDirectory = generateWxIdForLabel(_('Generate Link Directory'))
GenerateThumbnails = generateWxIdForLabel(_('Generate Thumbnail Directory'))
RenameElement = generateWxIdForLabel(_('Rename Tag'))
EditClasses = generateWxIdForLabel(_('Edit Tag Classes'))
EditNames = generateWxIdForLabel(_('Edit Names'))
HarvestURLs = generateWxIdForLabel(_('Harvest from URL...'))

## Importing
BrowseImportDirectory = generateWxIdForLabel(_('Browse'))

## MediaNamePane
RenameMedia = generateWxIdForLabel(_('Rename'))
ReuseLastClassification = generateWxIdForLabel(_('Reuse Last'))


# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
import datetime 
import re
import os.path
from io import StringIO
import logging
import gettext
from operator import itemgetter
## Contributed 
from collections import OrderedDict
# import exifread
# import wx
import wx.adv
#import wx.lib.calendar as wx_calendar
## nobi
from nobi.PartialDateTime import PartialDateTime
from nobi.SortedCollection import SortedCollection
from nobi.wx.Validator import TextCtrlIsIntValidator
## Project
from Model.MediaOrganization import MediaOrganization
from Model.MediaFilter import MediaFilter
from Model.Group import Group
from Model.MediaClassHandler import MediaClassHandler
import UI  # to access UI.PackagePath
from UI import GUIId
from UI.MediaFilterPane import FilterCondition
from Model.Image import Image


# Internationalization  # requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class OrganizationByDate(MediaOrganization):
    """A strategy to organize media by date.
    
    - Media is identified by year, month, day, number, and elements, all optional.
    - Media are stored in folders per year, per month, per day.
    - Elements are allowed on media names only.
    """



# Class Variables
    # format strings for date output
    FormatYear = '%04d'
    FormatMonth = '%02d'
    FormatYearMonth = (FormatYear + MediaOrganization.IdentifierSeparator + FormatMonth)
    FormatDay = '%02d'
    FormatYearMonthDay = (FormatYearMonth + MediaOrganization.IdentifierSeparator + FormatDay)
    UnknownDateName = (FormatYear % 0)
    # RE patterns to recognize dates
    YearString = r'(?:(?:' + UnknownDateName + ')|(?:(?:18|19|20)\d\d))'  # 4-digit year
    MonthString = r'[01]\d'  # 2-digit month
    DayString = r'[0123]\d'  # 2-digit day
    SeparatorString = r'[-_:/\.\\]'  # separator characters
    YearPattern = re.compile(r'(?<!\d)(%s)(?!\d)' % YearString)  # was: r'[/\\](%s)(?!\d)'
    MonthPattern = re.compile(r'(%s)%s(%s)(?!\d)' % (YearString, SeparatorString, MonthString))
    DayPattern = re.compile(r'(%s)(%s)(%s)\2(%s)(?!\d)' % (YearString, SeparatorString, MonthString, DayString))
    # Reduced patterns with 2-digit year
    ReducedYearString = r'[/\\](\d\d)'  # 2-digit year, only allowed at beginning of path component
    ReducedYearString2 = r'\d\d'  # 2-digit year, only allowed at beginning of path component
    ReducedYearPattern = re.compile(r'%s(?!\d)' % ReducedYearString)
    ReducedMonthPattern = re.compile(r'%s%s(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString))
    ReducedDayPattern = re.compile(r'%s(%s)(%s)\2(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString, DayString))
    # German Date
    GermanDayPattern2 = re.compile(r'(%s)(\.)(%s)\2(%s)' % (DayString, MonthString, YearString))  # was: YearString2
    ReducedGermanDayPattern2 = re.compile(r'(%s)(\.)(%s)\2(%s)' % (DayString, MonthString, ReducedYearString2))
    # Simplified pattern without separators
    SimpleDayPattern = re.compile(r'(%s)(%s)(%s)' % (YearString, MonthString, DayString))
    # Reordering
    ReorderSelectTop = 0
    ReorderSelectFollow = 1
    ReorderSelectBottom = 2
    ReorderLabelTop = _('at top')
    ReorderLabelFollow = _('with predecessor')
    ReorderLabelBottom = _('at bottom')



# Class Methods
    @classmethod
    def getDescription(cls):
        """Return a description of the organization. 
        """
        return(_('organized by date'))


    @classmethod
    def constructOrganizationPath(cls, **kwargs):
        """
        Dictionary kwargs
            Number year
            Number month
            Number day
        """
        if (('year' in kwargs)
            and kwargs['year']):
            year = kwargs['year']
        else:
            year = int(cls.UnknownDateName)
        result = (cls.FormatYear % year)
        if (('month' in kwargs)
            and kwargs['month']):
            month = kwargs['month']
            result = os.path.join(result, (cls.FormatYearMonth % (year, month)))
            if (('day' in kwargs)
                and kwargs['day']):
                result = os.path.join(result, 
                                      (cls.FormatYearMonthDay % (year, month, kwargs['day'])),
                                      (cls.FormatYearMonthDay % (year, month, kwargs['day'])))
            else:
                result = os.path.join(result, 
                                      (cls.FormatYearMonth % (year, month)))
        else:
            result = os.path.join(result, (cls.FormatYear % year))
        return(result)


    @classmethod
    def pathInfoForImport(self, importParameters, sourcePath, level, oldName, pathInfo):
        """Return a pathInfo mapping extended according to directory name oldName.
        """
        result = super(OrganizationByDate, self).pathInfoForImport(importParameters, sourcePath, level, oldName, pathInfo)
        return(result)

        
    @classmethod
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  # @UnusedVariable
        """
        """
        # determine date of image
        (year, month, day) = cls.deriveDate(importParameters.log, sourcePath, importParameters.getPreferPathDateOverExifDate())
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)
        extension = extension.lower() 
        # determine elements
        tagSet = cls.ImageFilerModel.deriveTags(importParameters, 
                                                sourcePath, 
                                                baseLength,
                                                illegalElements)
        if (importParameters.getMarkAsNew()):
            tagSet.add(MediaClassHandler.ElementNew)
        # ensure uniqueness via number
        newPath = cls.constructPath(rootDir=targetDir,
                                     year=year,
                                     month=month,
                                     day=day,
                                     elements=tagSet,
                                     extension=extension[1:],
                                     makeUnique=True)
        return(newPath)


    @classmethod
    def getGroupFromPath(cls, path):
        """Return the Group representing the given path. Create it if it does not exist.

        String path filename of a media folder
        Returns a MediaFiler.Group
        Raises KeyError 
        """
        group = cls.ImageFilerModel.getEntry(group=True, path=path)
        if (not group):
            (head, _) = os.path.split(path)  # @UnusedVariable
            parentGroup = cls.getGroupFromPath(head)
            if (not parentGroup):
                Logger.error('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % head)
                raise KeyError('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % head)
            group = Group(cls.ImageFilerModel, path)
            group.setParentGroup(parentGroup)
        return(group)


    @classmethod
    def ensureDirectoryExists(self, log, testRun, rootDirectory, year, month, day):  # @UnusedVariable 
        """Ensure the directory indicated by a date exists.
        
        StringIO log collects all messages.
        Boolean testRun indicates whether changes are allowed
        String rootDirectory contains the path to the model's root directory
        String year contains the year, or 'undated' 
        String or None month, day contain the month and day, if any 
        """
        newDir = rootDirectory
        if (year):  # for safety, should at least be "undated"
            newDir = os.path.join(newDir, year)
            if (month):
                newDir = os.path.join(newDir, "%s-%s" % (year, month))
                if (day):
                    newDir = os.path.join(newDir, "%s-%s-%s" % (year, month, day))
        Logger.debug('OrganizationByDate.ensureDirectoryExists(): Creating "%s"' % newDir)
        if (not testRun):
            if (not os.path.exists(newDir)):
                os.makedirs(newDir)
        return(newDir)


    @classmethod
    def deriveDate(self, log, path, preferPathDate=True):
        """Derive a date from the file at path. 
        
        If a date can be derived from the path, it takes precedence over a date derived from the EXIF image data. 
        year is guaranteed to contain a String; month and day may be None. 
        
        StringIO log collects messages.
        String path contains the file path.
        Boolean preferPathDate indicates that a date derived from path takes precedence over a date derived from EXIF data
        
        Returns a tuple (year, month, day) which either are a Number or None (if not defined). 
        """
        # default values
        year = int(self.UnknownDateName)
        month = None
        day = None
        datesDiffer = False
        exifMoreSpecific = False
        # determine dates
        exifDate = self.deriveDateFromFile(log, path)
        pathDate = self.deriveDateFromPath(log, path)
        if ((exifDate[0] != None)
            and (pathDate[0] != self.UnknownDateName)
            and ((exifDate[0] != pathDate[0])
                 or (exifDate[1] != pathDate[1])
                 or (exifDate[2] != pathDate[2]))):
            datesDiffer = True
        # select date
        if (preferPathDate):  # date derived from path takes precedence
            if (pathDate[0] != self.UnknownDateName):
                (year, month, day, dummy) = pathDate
                # if exif date is more specific than path date, use it
                if (year == exifDate[0]):
                    if (month == None):
                        exifMoreSpecific = True
                        (month, day) = exifDate[1:]
                    elif (month == exifDate[1]):
                        if (day == None):
                            exifMoreSpecific = True
                            day = exifDate[2]
            elif (exifDate[0] != None):
                (year, month, day) = exifDate
        else:  # date derived from EXIF takes precedence
            if (exifDate[0]):
                (year, month, day) = exifDate
            elif (pathDate[0] != self.UnknownDateName):
                (year, month, day, dummy) = pathDate
        if (exifMoreSpecific):
            Logger.debug('OrganizationByDate.deriveDate(): EXIF (%s) more specific than path (%s) in file "%s"\n' % (exifDate, pathDate, path))
        elif (datesDiffer):
            Logger.debug('OrganizationByDate.deriveDate(): EXIF (%s) and path (%s) differ in file "%s"\n' % (exifDate, pathDate, path))
        if (year):
            year = int(year)
        if (month):
            month = int(month)
        if (day):
            day = int(day)
        return(year, month, day)


    @classmethod
    def deriveDateFromFile(self, log, path):  # @UnusedVariable
        """Determine date of image from EXIF information.
        
        StringIO log collects messages
        String path contains the absolute filename
        
        Returns a triple (year, month, day)
            which either contains year, month, and day as String
            or contains None for each entry
        """
        # TODO: Make the exclusion conditions configurable
        exclusions = {'Model': 'MS Scanner',
                      'Software': 'Paint Shop Photo Album'}
        if ((os.path.isfile(path)) 
            and (path[-4:].lower() == '.jpg')): 
            exifTags = Image.getMetadataFromPath(path)
            for (tag, value) in exclusions.items():
                if ((tag in exifTags)
                    and (0 <= exifTags[tag].find(value))):
                    Logger.debug('OrganizationByDate.deriveDateFromFile(): Ignoring EXIF data for "%s"\n  because %s=%s' % (path, tag, value))
                    return(None, None, None)
            dateTags = set((tag for tag in exifTags.keys() if ('Date' in tag)))
            digitizedTags = set(tag for tag in dateTags if (('Original' in tag) or ('Digitized' in tag)))
            if (0 == len(digitizedTags)):
                digitizedTags = dateTags
            if (0 == len(digitizedTags)):
                Logger.debug('OrganizationByDate.deriveDateFromFile(): No tag named "*Date*" found')
                return(None, None, None)
            for key in digitizedTags:
                Logger.debug('OrganizationByDate.deriveDateFromFile(): Relevant EXIF tag "%s" in "%s"' % (key, path))
                value = exifTags[key]
                match = self.DayPattern.search(str(value))
                if (match):
                    year = match.group(1)
                    month = match.group(3)
                    day = match.group(4)
                    if (year == self.UnknownDateName):
                        month = None
                        day = None
                    Logger.debug('OrganizationByDate.deriveDateFromFile(): Recognized date (%s, %s, %s) in EXIF data of file "%s"\n' % (year, month, day, path)) 
                    return(year, month, day)
                else:
                    Logger.debug('OrganizationByDate.deriveDateFromFile(): EXIF tag %s contains illegal date %s' % (key, value))
        Logger.debug('OrganizationByDate.deriveDateFromFile(): No date found in EXIF data')
        return(None, None, None)


    @classmethod
    def deriveDateFromPath(cls, log, path):  # @UnusedVariable
        """Determine the date of the file PATH. 
        
        StringIO log is used to report progress. 
        String path contains the absolute filename.  

        Return a triple (year, month, day, rest) where 
            year, month, and day are either String or None 
            rest is a String containing the rest of path not consumed by the match
            
        #TODO: Use file creation/modification date is none given on path
        """
        # intialize variables
        year = None
        month = None
        day = None
        Logger.debug('OrganizationByDate.deriveDateFromPath(): Inspecting "%s"' % path)
        # search for date
        match = cls.DayPattern.search(path)
        usingReducedPattern = False
        if (match == None):
            usingReducedPattern = True
            match = cls.ReducedDayPattern.search(path)
        if (match):
            Logger.debug('OrganizationByDate.deriveDateFromPath(): Day pattern matched')
            if (match.group(2) == '.'):  # German date format DD.MM.YY(YY)
                day = match.group(1)
                month = match.group(3)
                year = match.group(4)
            else:  # YY(YY)-MM-DD
                year = match.group(1)
                month = match.group(3)
                day = match.group(4)
            if (usingReducedPattern):
                assert (len(year) == 2), ('Reduced year "%s" too long in "%s"' % (year, path)) 
                year = cls.expandReducedYear(year)
            matched = (cls.FormatYearMonthDay % (int(year), int(month), int(day)))
            matchEnd = match.end()
        else:
            match = cls.SimpleDayPattern.search(path)
            if (match):
                Logger.debug('OrganizationByDate.deriveDateFromPath(): Simple day pattern matched')
                year = match.group(1)
                month = match.group(2)
                day = match.group(3)
                matched = (cls.FormatYearMonthDay % (int(year), int(month), int(day)))
                matchEnd = match.end()
            else:
                match = cls.MonthPattern.search(path)
                usingReducedPattern = False
                if (match == None):
                    #log.write('Month pattern did not match in "%s"\n' % path)
                    usingReducedPattern = True
                    match = cls.ReducedMonthPattern.search(path)
                if (match):
                    Logger.debug('OrganizationByDate.deriveDateFromPath(): Month pattern matched')
                    year = match.group(1)
                    if (usingReducedPattern):  # fix two-digit year
                        assert (len(year) == 2), ('Reduced year "%s" too long in "%s"' % (year, path)) 
                        year = cls.expandReducedYear(year)
                    month = match.group(2)
                    matched = (cls.FormatYearMonth % (int(year), int(month)))
                    matchEnd = match.end()
                else: 
                    match = cls.YearPattern.search(path)
                    usingReducedPattern = False
    # A number starting the filename may be a year or just a counter - don't interpret as year
    #                 if (match == None):
    #                     usingReducedPattern = True
    #                     match = cls.ReducedYearPattern.search(path)
                    if (match):
                        Logger.debug('OrganizationByDate.deriveDateFromPath(): Year pattern matched')
                        year = match.group(1)
                        if (usingReducedPattern):
                            year = cls.expandReducedYear(year)
                        matched = (cls.FormatYear % int(year))
                        matchEnd = match.end()
                    else:
                        (year, month, day) = cls.deriveDateWithMonthFromPath(log, path)
                        if (year):
                            matched = ''
                            matchEnd = -1
                        else:
                            year = cls.UnknownDateName
                            matched = ''
                            matchEnd = -1
        Logger.debug('OrganizationByDate.deriveDateFromPath(): Recognized (%s, %s, %s) in path "%s"' % (year, month, day, path)) 
        # skip to last occurrence of match
        rest = path
        while (0 <= matchEnd):  
            rest = rest[matchEnd:]
            matchBegin = rest.find(matched)
            if (0 <= matchBegin):
                matchEnd = (matchBegin + len(matched))
            else: 
                matchEnd = -1
        return (year, month, day, rest)


    @classmethod
    def deriveDateWithMonthFromPath(cls, log, path):  # @UnusedVariable
        """Determine the date of a media file from its path. 
        
        StringIO log is used to report progress. 
        String path contains the absolute filename.

        Return a triple (year, month, day, rest) where 
            year, month, and day are either String or None 
            rest is a String containing the rest of path not consumed by the match
        """
        # intialize variables
        year = None
        month = None
        day = None
        ms = [u'Januar', u'Februar', u'März', u'April', u'Mai', u'Juni', u'Juli', u'August', u'September', u'Oktober', u'November', u'Dezember']
        for m in ms: 
            pattern = ('%s\W*(\d\d)' % m)
            match = re.search(pattern, path)
            if (match):
                year = cls.expandReducedYear(match.group(1))
                month = (cls.FormatMonth % (ms.index(m) + 1))
                break
            else: 
                pattern = ('%s[.]\W*(\d\d)' % m[0:3])
                match = re.search(pattern, path)
                if (match):
                    year = cls.expandReducedYear(match.group(1))
                    month = (cls.FormatMonth % (ms.index(m) + 1))
                    break
        return(year, month, day)


    @classmethod
    def expandReducedYear(cls, year):
        """Year has been specified with two digits only (i.e., 0-99). Prefix '19' or '20' as appropriate.
        
        String year
        Return String with a four digit year
        """
        currentYear = (datetime.date.today().year % 100)
        if (int(year) <= currentYear):  # add 2000 only if the result is earlier than current year
            year = ('20' + year)
        else:
            year = ('19' + year)
        return(year)


    @classmethod
    def registerMoveToLocation(cls, pathInfo):
        """overwrite MediaOrganization.registerMoveToLocation()
        """
        register = OrderedDict()
        for value in ('year', 'month', 'day'):
            if (value in pathInfo):
                register[value] = pathInfo[value]
        super(OrganizationByDate, cls).registerMoveToLocation(register)


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        
        Adds year, month, day fields.
        """
        # year
        aMediaNamePane.yearInput = wx.TextCtrl(aMediaNamePane, 
                                               size=wx.Size(80,-1), 
                                               style=wx.TE_PROCESS_ENTER,
                                               validator=TextCtrlIsIntValidator(label=_('Year'), 
                                                                                minimum=1800, 
                                                                                maximum=2099,
                                                                                emptyAllowed=True))
        aMediaNamePane.yearInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.yearInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.IdentifierSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # month
        aMediaNamePane.monthInput = wx.TextCtrl(aMediaNamePane, 
                                                size=wx.Size(40,-1), 
                                                style=wx.TE_PROCESS_ENTER,
                                                validator=TextCtrlIsIntValidator(label=_('Month'), 
                                                                                 minimum=1, 
                                                                                 maximum=12,
                                                                                 emptyAllowed=True))
        aMediaNamePane.monthInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.monthInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.IdentifierSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # day
        aMediaNamePane.dayInput = wx.TextCtrl(aMediaNamePane, 
                                              size=wx.Size(40,-1), 
                                              style=wx.TE_PROCESS_ENTER,
                                              validator=TextCtrlIsIntValidator(label=_('Day'), 
                                                                               minimum=1, 
                                                                               maximum=31,
                                                                               emptyAllowed=True))
        aMediaNamePane.dayInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.dayInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # generic 
        MediaOrganization.initNamePane(aMediaNamePane)


    @classmethod
    def initFilterPane(cls, aMediaFilterPane):
        """Add controls to MediaFilterPane to represent the organization's search capabilities.
        
        Adds date filter.
        """
        super(OrganizationByDate, cls).initFilterPane(aMediaFilterPane)
        aMediaFilterPane.addCondition(DateFilter(aMediaFilterPane))
        aMediaFilterPane.addSeparator()

    
# Lifecycle
    def __init__(self, anEntry, aPath):
        """
        """
        # inheritance
        MediaOrganization.__init__(self, anEntry, aPath)
        # internal state
        self.timeTaken = None  # for Singles: capture time
        self.reorderedGroup = None  # for Groups: last re-ordered group
        self.undoReorderList = None  # for Groups: undo last reordering



# Setters
    def setIdentifiersFromPath(self, path):
        """Set year, month, day (if any) from path, and return remaining part of path.
        
        Returns a String containing the remaining part of PATH to the right of the last identifier found.
        """
#         (year, month, day, rest) = self.deriveDateFromPath(StringIO.StringIO(), path)
        (year, month, day, rest) = self.deriveDateFromPath(StringIO(), path)  # Python 3 
        self.year = year
        self.month = month
        self.day = day
        year = (int(year) if year else None)
        month = (int(month) if month else None)
        day = (int(day) if day else None)
        try:
            self.dateTaken = PartialDateTime(year, month, day)
        except Exception as e:
            self.dateTaken = PartialDateTime(None, None, None)
        return(rest)



# Getters
    def isUnknown(self):
        """Return whether self is incompletely specified.

        Return Boolean
        """
        return(self.getYear == OrganizationByDate.UnknownDateName)


    def matches(self, **kwargs):
        """override MediaOrganization.matches
        """
        return(((not 'year' in kwargs)
                or (kwargs['year'] == None)
                or (kwargs['year'] == self.getYearString())
                or (kwargs['year'] == self.getYear()))
               and ((not 'month' in kwargs)
                or (kwargs['month'] == None)
                or (kwargs['month'] == self.getMonthString())
                or (kwargs['month'] == self.getMonth()))
               and ((not 'day' in kwargs)
                or (kwargs['day'] == None)
                or (kwargs['day'] == self.getDayString())
                or (kwargs['day'] == self.getDay())))


    def getPathInfo(self, filtering=False):
        """override MediaOrganization.getPathInfo(self)
        """
        result = MediaOrganization.getPathInfo(self, filtering)
        if (self.getYear() != OrganizationByDate.UnknownDateName):
            result['year'] = self.getYear()
            if (self.getMonth()):
                result['month'] = self.getMonth()
                if (self.getDay()):
                    result['day'] = self.getDay()
        return(result)


    def getTimeTaken(self):
        """Return the time self was taken. 
        
        Works for single images with EXIF info only.
        
        TODO: Move to Single, and subclasses Image and Movie.
        
        Return datetime.time or None
        """
        if (not self.timeTaken):
            if (self.getContext().getExtension() == 'jpg'): 
                exifTags = self.getContext().getMetadata()
                if (('Model' in exifTags)
                    and (exifTags['Model'] == 'MS Scanner')):
                    Logger.debug('OrganizationByDate.getTimeTaken(): Ignoring EXIF data because Model=MS Scanner')
                    return(None)
                if (('Software' in exifTags)
                    and (0 <= exifTags['Software'].find('Paint Shop Photo Album'))):
                    Logger.debug('OrganizationByDate.getTimeTaken(): Ignoring EXIF data because Software=Paint Shop Photo Album')
                    return (None)
                for key in exifTags:
                    if ('DateTime' in key):
                        Logger.debug('OrganizationByDate.getTimeTaken(): Relevant EXIF tag "%s" in "%s"' % (key, self.context.getPath()))
                        value = str(exifTags[key])
                        match = re.match('(\d\d\d\d):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)', value)
                        timestamp = None
                        if (match):
                            (year, month, day, hour, minute, second) = match.groups()
                            if (not (None in (year, month, day, hour, minute, second))):
                                year = int(year)
                                month = int(month)
                                day = int(day)
                                hour = int(hour)
                                minute = int(minute)
                                second = int(second)
                                timestamp = datetime.datetime(year, month, day, hour, minute, second)
                            else:
                                Logger.warning('OrganizationByDate.getTimeTaken(): Invalid time "%s" in EXIF tag "%s" of file "%s"' % (value, key, self.getContext().getPath()))
                        if (timestamp == None):
                            try:
                                timestamp = datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                timestamp = datetime.datetime.fromisoformat(value)
                            except ValueError as e:
                                Logger.warning('OrganizationByDate.getTimeTaken(): EXIF tag "%s" contains illegal date %s (Exception follows)\n%s' % (key, value, e))
                        if (timestamp):
                            self.timeTaken = timestamp.time()
                            Logger.debug('OrganizationByDate.getTimeTaken(): Recognized time %s in EXIF data of file "%s"' % (self.timeTaken, self.context.getPath())) 
                            return(self.timeTaken)
                Logger.info('OrganizationByDate.getTimeTaken(): No time found for "%s"' % self.context.getPath())
            else:
                Logger.info('OrganizationByDate.getTimeTaken(): No time available for "%s"' % self.context.getPath())
        return(self.timeTaken)


    def extendContextMenu(self, menu):
        """Extend the context menu to contain functions relevant for organization by date.

        MediaFiler.Entry.Menu menu 
        Return nobi.wx.Menu (which is a wx.Menu)
        """
        if (self.getContext().isGroup()):
            if ((self.reorderedGroup == self.getContext()) 
                and (self.undoReorderList)):
                menu.insertAfterId(GUIId.SelectMoveTo,
                                   newText=GUIId.FunctionNames[GUIId.UndoReorder],
                                   newId=GUIId.UndoReorder)
            else:
                menu.insertAfterId(GUIId.SelectMoveTo, 
                                  newText=GUIId.FunctionNames[GUIId.ReorderByTime],
                                  newId=GUIId.ReorderByTime)
        else:
            menu.insertAfterId(GUIId.SelectMoveTo, 
                               newText=GUIId.FunctionNames[GUIId.AssignNumber],
                               newMenu=self.deriveRenumberSubMenu())
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions to handle the menu items added in extendContextMenu()
        """
        if (menuId == GUIId.ReorderByTime):
            return(self.onReorderByTime(parentWindow))
        elif (menuId == GUIId.UndoReorder):
            return(self.onUndoReorder(parentWindow))
        else:
            self.undoReorderList = None
            return(super(OrganizationByDate, self).runContextMenuItem(menuId, parentWindow))


    def getDateTaken(self):
        if (self.dateTaken == None):
            Logger.error('OrganizationByDate.getDateTaken(): No date found for "%s"' % self.context.getPath())
        return(self.dateTaken)


    def getYear(self):
        if (((self.year != None)
             and (self.dateTaken != None)
             and (int(self.year) != self.dateTaken.getYear()))
            or ((self.year == None)
                and self.dateTaken.getYear())):
            Logger.error('OrganizationByDate.getYear(): explicit and PartialDateTime year do not match')
        if (self.year == None):
            return(None)
        else:
            return(int(self.year))

    
    def getYearString(self):
        if (self.dateTaken
            and self.dateTaken.getYear()):
            return(OrganizationByDate.FormatYear % self.dateTaken.getYear())
        else:
            return(OrganizationByDate.UnknownDateName)


    def getMonth(self):
        if (((self.month != None)
             and (self.dateTaken != None)
             and (int(self.month) != self.dateTaken.getMonth()))
            or ((self.month == None)
                and (self.dateTaken != None)
                and self.dateTaken.getMonth())):
            Logger.error('OrganizationByDate.getMonth(): explicit and PartialDateTime month do not match')
        if (self.month == None):
            return(None)
        else:
            return(int(self.month))
    

    def getMonthString(self):
        if (self.dateTaken
            and self.dateTaken.getMonth()):
            return(OrganizationByDate.FormatMonth % self.dateTaken.getMonth())
        else:
            return(u'')

    
    def getDay(self):
        if (((self.day != None)
             and (self.dateTaken != None)
             and (int(self.day) != self.dateTaken.getDay()))
            or ((self.day == None)
                and (self.dateTaken != None)
                and self.dateTaken.getDay())):
            Logger.error('OrganizationByDate.getDay(): explicit and PartialDateTime day do not match')
        if (self.day == None):
            return(None)
        else:
            return(int(self.day))    


    def getDayString(self):
        if (self.dateTaken
            and self.dateTaken.getDay()):
            return(OrganizationByDate.FormatDay % self.dateTaken.getDay())
        else:
            return(u'')



# Other API Funcions
    def renameGroup(self, processIndicator=None, filtering=False, **newPathInfo):
        """Rename self's context according to the specified changes.
        
        processIndicator
        Boolean filtering
        dict newPathInfo
            elements
            :
            organization-specific parameters
        Return the Entry to be selected after the renaming
        
        TODO: fold into superclass renameGroup()
        """
        print('OrganizationByDate.renameGroup(): deprecated!')
        newYear = (newPathInfo['year'] if ('year' in newPathInfo) else None)
        newMonth = (newPathInfo['month'] if ('month' in newPathInfo) else None)
        newDay = (newPathInfo['day'] if ('day' in newPathInfo) else None)
        # ensure group exists
        if ((newYear == self.getYear())  # TODO: replace by match()?!
            and (newMonth == self.getMonth())
            and (newDay == self.getDay())):
            newParent = self.getContext()
        else:
            model = self.__class__.ImageFilerModel
            newParent = model.getEntry(group=True, year=newYear, month=newMonth, day=newDay)
            if (not newParent):
                newParent = Group.createAndPersist(model, 
                                                   self.__class__.constructPath(year=newYear, month=newMonth, day=newDay))
        otherNewParent = self.findGroupFor(**newPathInfo)
        if (newParent != otherNewParent):
            print('OrganizationByDate.renameGroup(): Different new parents found!')
        # move subentries to new group
        for subEntry in self.getContext().getSubEntries(filtering=filtering):
            pathInfo = subEntry.getOrganizer().getPathInfo()
            if ('elements' in newPathInfo):
                pathInfo['elements'].update(newPathInfo['elements'])
            if ('classesToRemove' in newPathInfo):
                pathInfo['classesToRemove'] = newPathInfo['classesToRemove']
            if ('removeIllegalElements' in newPathInfo): 
                pathInfo['removeIllegalElements'] = newPathInfo['removeIllegalElements']
            if (newParent != self.getContext()):
                pathInfo['year'] = newYear
                pathInfo['month'] = newMonth
                pathInfo['day'] = newDay
                pathInfo['makeUnique'] = True
            subEntry.renameTo(**pathInfo)
        # check whether old group still has subentries
        if (0 == len(self.getContext().getSubEntries())):
            self.getContext().remove()
        return(newParent)


    def getRenameList(self, newParent, pathInfo, filtering=True):
        """Create a list of <entry, pathInfo> to move self's subentries to newParent.
        """
        if (not self.getContext().isGroup()):
            raise ValueError('OrganizationByName.getRenameList(): Entry "%s" is not a Group!' % self)
        # create list of subentries and their new pathInfo 
        result = []
        for subEntry in self.getContext().getSubEntries(filtering=filtering):
            newPathInfo = subEntry.getOrganizer().getPathInfo()
            for orgId in ['year', 'month', 'day']:
                if ((orgId in pathInfo)
                    and (pathInfo[orgId])):
                    newPathInfo[orgId] = pathInfo[orgId]
                else:
                    del newPathInfo[orgId]
            if ('classesToRemove' in pathInfo):
                newPathInfo['classesToRemove'] = pathInfo['classesToRemove'] 
            if ('removeIllegalElements' in pathInfo):
                newPathInfo['removeIllegalElements'] = pathInfo['removeIllegalElements'] 
            if ('elements' in pathInfo):
                newTags = self.getModel().getClassHandler().combineTagsWithPriority(subEntry.getTags(), pathInfo['elements'])
                newPathInfo['elements'] = newTags 
            pair = (subEntry.getOrganizer(), newPathInfo)
            result.append(pair)
        return(result)


    def findGroupFor(self, **pathInfo):
        """override MediaOrganization.findGroupFor()
        """
        year = None
        month = None
        day = None
        if (('year' in pathInfo)
            and (pathInfo['year'])):
            year = pathInfo['year']
            if (('month' in pathInfo)
                and (pathInfo['month'])):
                month = pathInfo['month']
                if (('day' in pathInfo)
                    and (pathInfo['day'])):
                    day = pathInfo['day']
        if (self.matches(**pathInfo)):
            if (self.getContext().isGroup()):
                result = self.getContext()
            else: 
                result = self.getContext().getParentGroup()
        else:
            model = self.__class__.ImageFilerModel
            result = model.getEntry(year=year, month=month, day=day)
            if (result == None):
                result = Group.createAndPersist(model, year=year, month=month, day=day)
        return(result)


    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        MediaOrganization.setValuesInNamePane(self, aMediaNamePane)
        aMediaNamePane.yearInput.SetValue(self.getYearString())
        aMediaNamePane.monthInput.SetValue(self.getMonthString())
        aMediaNamePane.dayInput.SetValue(self.getDayString())


    def getValuesFromNamePane(self, aMediaNamePane):
        """
        
        Return Dictionary mapping String to values
            or None if field values are illegal
        """
        result = MediaOrganization.getValuesFromNamePane(self, aMediaNamePane)
        year = aMediaNamePane.yearInput.GetValue()
        if (year != ''):
            try:
                result['year'] = int(year)
            except:
                Logger.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret year string "%s" as int' % year)
                return(None)
        month = aMediaNamePane.monthInput.GetValue()
        if (month != ''):
            try:
                result['month'] = int(month)
            except:
                Logger.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret month string "%s" as int' % month)
                return(None)
        day = aMediaNamePane.dayInput.GetValue()
        if (day != ''):
            try:
                result['day'] = int(day)
            except: 
                Logger.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret day string "%s" as int' % day)
                return(None)
        return(result)



# Event Handlers
    def onReorderByTime(self, parentWindow):
        """
        """
        dlg = wx.Dialog(parentWindow, wx.ID_ANY, _('Reorder by Time Taken'))
        dlgSizer = wx.BoxSizer(orient=wx.VERTICAL)
        # selection of how to handle media without time taken
        rb = wx.RadioBox(dlg,
                         label=_('Media without capture time placed'), 
                         choices=[OrganizationByDate.ReorderLabelTop,
                                  OrganizationByDate.ReorderLabelFollow,
                                  OrganizationByDate.ReorderLabelBottom],
                         majorDimension=1, 
                         style=(wx.RA_SPECIFY_COLS))
        rb.SetSelection(OrganizationByDate.ReorderSelectFollow)
        dlgSizer.Add(rb, border=5)
        # renumbering step width
        fldSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        fldSizer.Add(wx.StaticText(dlg, label=_('Step Width for Renumbering:')))
        stepWidthField = wx.SpinCtrl(dlg, min=1, max=20, initial=1, size=(50, 20))
        fldSizer.Add(stepWidthField)
        dlgSizer.Add(fldSizer)
        # final buttons
        line = wx.StaticLine(dlg,
                             size=(20,-1), 
                             style=wx.LI_HORIZONTAL)
#         dlgSizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        dlgSizer.Add(line, 0, wx.GROW|wx.RIGHT|wx.TOP, 5)
        btnSizer = wx.StdDialogButtonSizer()        
        btn = wx.Button(dlg, wx.ID_OK)
        btn.SetDefault()
        btnSizer.AddButton(btn)
        btn = wx.Button(dlg, wx.ID_CANCEL)
        btnSizer.AddButton(btn)
        btnSizer.Realize()
#         dlgSizer.Add(btnSizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        dlgSizer.Add(btnSizer, 0, wx.ALL, 5)
        dlg.SetSizerAndFit(dlgSizer)
        # show dialog
        if (dlg.ShowModal() == wx.ID_OK):
            self.reorderByTime(rb.GetSelection(), stepWidthField.GetValue())
        dlg.Destroy()


    def onUndoReorder(self, parentWindow):
        """
        """
        result = None
        dlg = wx.MessageDialog(parentWindow, 
                               _('Undo the last reorder by time command?'),
                               _('Undo Reordering?'),
                               (wx.YES_NO | wx.ICON_INFORMATION))
        if (dlg.ShowModal() == wx.ID_YES):
            if (self.getContext().model.renameList(self.undoReorderList)):
                result = _('Reordering undone')
            else:
                result = _('Undoing reordering failed!')
            self.undoReorderList = None            
        dlg.Destroy()
        return(result)



# Internal - to change without notice
    def reorderByTime(self, handleUntimedPolicy, stepWidth):
        """Reorder subentries of self's context by time taken, earlierst first.
        
        Increment numbers by stepWidth.
        
        Media without a time taken (i.e., videos and images without EXIF info) are sorted according to handleUntimedPolicy:
        ReorderSelectTop: 0: they appear at top (first microseconds of day), in current relative order
        ReorderSelectFollow: 1: they move with their predecessor
        ReorderSelectBottom: 2: they appear at bottom (last microseconds of day), in current relative order
        
        Number handleUntimedPolicy
        Number stepWidth
        """
        if (stepWidth < 1):
            raise ValueError('OrganizationByDate.reorderByTime(): stepWidth must be greater than 0')
        if (not (handleUntimedPolicy in [OrganizationByDate.ReorderSelectTop,
                                    OrganizationByDate.ReorderSelectFollow, 
                                    OrganizationByDate.ReorderSelectBottom])):
            raise ValueError('OrganizationByDate.reorderByTime(): Illegal policy %d to handle media without timestamp!' % handleUntimedPolicy)
        Logger.debug('OrganizationByDate.reorderByTime(): Reordering subentries of %s' % self.getContext())
        resorted = SortedCollection(key=itemgetter(1))
        nextTimeForUntimedMedia = datetime.time(hour=0, minute=0, second=0, microsecond=1)
        untimedMediaAtBottom = [] # 
        for subEntry in [e for e in self.getContext().getSubEntries(False) if (not e.isGroup())]:
            sortTime = subEntry.organizer.getTimeTaken()
            if (sortTime):  # entry has a timestamp
                Logger.debug('OrganizationByDate.reorderByTime(): Found %s for "%s"' % (sortTime, subEntry.getPath()))
                resorted.insert((subEntry, sortTime))
                if (handleUntimedPolicy == OrganizationByDate.ReorderSelectFollow):
                    nextTimeForUntimedMedia = datetime.time(hour=sortTime.hour,
                                                            minute=sortTime.minute,
                                                            second=sortTime.second,
                                                            microsecond=1)
                    if (nextTimeForUntimedMedia <= sortTime):
                        Logger.error('Expected %s <= %s, but that''s false' % (sortTime, nextTimeForUntimedMedia))
            else:  # entry has no timestamp
                if (handleUntimedPolicy == OrganizationByDate.ReorderSelectTop):
                    Logger.debug('OrganizationByDate.reorderByTime(): Using %s for "%s"' % (nextTimeForUntimedMedia, subEntry.getPath()))
                    resorted.insert((subEntry, nextTimeForUntimedMedia))
                    nextTimeForUntimedMedia = datetime.time(hour=nextTimeForUntimedMedia.hour,
                                                            minute=nextTimeForUntimedMedia.minute,
                                                            second=nextTimeForUntimedMedia.second,
                                                            microsecond=(nextTimeForUntimedMedia.microsecond + 1))
                elif (handleUntimedPolicy == OrganizationByDate.ReorderSelectFollow):                    
                    Logger.debug('OrganizationByDate.reorderByTime(): Using %s for "%s"' % (nextTimeForUntimedMedia, subEntry.getPath()))
                    resorted.insert((subEntry, nextTimeForUntimedMedia))
                    nextTimeForUntimedMedia = datetime.time(hour=nextTimeForUntimedMedia.hour,
                                                            minute=nextTimeForUntimedMedia.minute,
                                                            second=nextTimeForUntimedMedia.second,
                                                            microsecond=(nextTimeForUntimedMedia.microsecond + 1))
                else:  # (handleUntimedPolicy == OrganizationByDate.ReorderSelectBottom):
                    Logger.debug('OrganizationByDate.reorderByTime(): Moving "%s" to end' % subEntry.getPath())
                    untimedMediaAtBottom.append(subEntry)
        for subEntry in untimedMediaAtBottom:
            sortTime = datetime.time(23, 
                                     59,  
                                     59, 
                                     (100000 - len(untimedMediaAtBottom) + untimedMediaAtBottom.index(subEntry)))
            Logger.debug('OrganizationByDate.reorderByTime(): Using %s for "%s"' % (sortTime, subEntry.getPath()))
            resorted.insert((subEntry, sortTime))
        Logger.debug('OrganizationByDate.reorderByTime(): sorted %s subentries' % len(resorted))
        newIndex = 1
        doList = []
        self.undoReorderList = []
        for (subEntry, time) in resorted:
            pathInfo = subEntry.getOrganizer().getPathInfo()
            pathInfo['number'] = newIndex
            newPath = subEntry.getOrganizer().__class__.constructPath(**pathInfo)
            newIndex = (newIndex + stepWidth)
            if (subEntry.getPath() != newPath):
                Logger.debug('OrganizationByDate.reorderByTime(): At %s, reordering\n   %s to\n  %s' % (time, subEntry.getPath(), newPath))
                doList.append((subEntry, subEntry.getPath(), newPath))
                self.undoReorderList.append((subEntry, newPath, subEntry.getPath()))
        Logger.debug('OrganizationByDate.reorderByTime(): sorted %s subentries, now renaming' % len(resorted))
        if (self.context.model.renameList(doList)):
            return(_('%s media reordered') % len(doList))
        else:
            return(_('Reordering failed!'))



class FilterByDate(MediaFilter):
    """A filter for media organized by date, i.e., including date.
    """


# Class Constants
    ConditionKeyDateFrom = 'fromDate'
    ConditionKeyDateTo = 'toDate'    


# Class Methods
    @classmethod
    def getConditionKeys(cls):
        """overwrite MediaFilter.getConditionKeys()"""
        keys = super(FilterByDate, cls).getConditionKeys()
        keys.extend([FilterByDate.ConditionKeyDateFrom,
                     FilterByDate.ConditionKeyDateTo])
        return(keys)


# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        super(FilterByDate, self).__init__(model)
        # internal state
        self.conditionMap[FilterByDate.ConditionKeyDateFrom] = None
        self.conditionMap[FilterByDate.ConditionKeyDateTo] = None


# Setters
#     def clear(self):
#         """override MediaFilter.clear()"""
#         super(FilterByDate, self).clear()
#         self.setConditions(fromDate=None,  # TODO: reduce to one call to setConditions(): define allFilterConditions() to return list of criteria, and iterate over them in MediaFilter.clear()
#                            toDate=None)
#         Logger.debug('FilterByDate.clear() finished as %s' % self)


#     def setConditionsAndCalculateChange(self, **kwargs):
#         """override MediaFilter.setConditionsAndCalculateChange()"""
#         changed = super(FilterByDate, self).setConditionsAndCalculateChange(**kwargs)
# #         # TODO: redundant?
# #         for key in [FilterByDate.ConditionKeyDateFrom, FilterByDate.ConditionKeyDateTo]:
# #             if ((key in kwargs)
# #                 and (kwargs[key] != self.conditionMap[key])):
# #                 self.conditionMap[key] = kwargs[key]
# #                 changed = True
#         return(changed)


# Getters
    def getDateFrom(self):
        return(self.conditionMap[FilterByDate.ConditionKeyDateFrom])


    def getDateTo(self):
        return(self.conditionMap[FilterByDate.ConditionKeyDateTo])


    def getDateRange(self):
        return(self.getDateFrom(), self.getDateTo())


    def __repr__(self):
        """override MediaFilter.__repr__()"""
        result = super(FilterByDate, self).__repr__()  # ends with ')'
        conditions = ''
        if (self.getDateFrom() != None):
            conditions = ('after %s' % self.getDateFrom())
        if (self.getDateTo() != None):
            if (0 < len(conditions)):
                conditions = (conditions + ' ')
            conditions = conditions + ('before %s' % self.getDateTo())
        result = (result[:-1] + conditions + ')')
        return(result)


    def filteredByConditions(self, entry):
        """override MediaFilter.filteredByConditions()"""
        dateFrom = self.getDateFrom()
        if (dateFrom
            and (entry.getOrganizer().getDateTaken()) < dateFrom):
            Logger.debug('FilterByDate.isFiltered(): From date %s filters %s' % (dateFrom, entry))
            return(True)
        dateTo = self.getDateTo()
        if (dateTo
            and (dateTo < entry.getOrganizer().getDateTaken())):
            Logger.debug('FilterByDate.isFiltered(): To date filters %s' % entry)
            return(True)
        return(super(FilterByDate, self).filteredByConditions(entry))



class DateFilter(FilterCondition):
    """Represents a filter for a media's date.
    """
    def __init__(self, parent):
        FilterCondition.__init__(self, parent, _('Date Taken'))
        self.fromDatePicker = wx.adv.DatePickerCtrl(parent, style=(wx.adv.DP_DROPDOWN | wx.adv.DP_ALLOWNONE))
        self.fromDatePicker.Bind(wx.adv.EVT_DATE_CHANGED, self.onChange, self.fromDatePicker)
        self.toDatePicker = wx.adv.DatePickerCtrl(parent, style=(wx.adv.DP_DROPDOWN | wx.adv.DP_ALLOWNONE))
        self.toDatePicker.Bind(wx.adv.EVT_DATE_CHANGED, self.onChange, self.toDatePicker)


    def getConditionControls(self):
        return([self.fromDatePicker, self.toDatePicker])


    def onChange(self, event):
        """
        If there are problems retrieving the value using GetValue(), try Navigate() first:
        https://stackoverflow.com/questions/1568491/wx-datepickerctrl-in-dialog-ignores-value-entered-after-hitting-return-on-wxgtk
        """
        wx.BeginBusyCursor()
        source = event.GetEventObject()
        (fromDate, toDate) = self.filterModel.getDateRange()  # need to pass back if unchanged
        if (source == self.fromDatePicker):
            wxDate = self.fromDatePicker.GetValue()
            if (wxDate.IsValid()):
                fromDate = datetime.date.fromisoformat(wxDate.FormatISODate())
            else:
                fromDate = None
            Logger.debug('DateFilter.onChange(): Changing from date to %s' % fromDate)
        elif (event.GetEventObject() == self.toDatePicker):
            wxDate = self.toDatePicker.GetValue()
            if (wxDate.IsValid()):
                toDate = datetime.date.fromisoformat(wxDate.FormatISODate())
            else:
                toDate = None
            Logger.debug('DateFilter.onChange(): Changing to date to %s' % toDate)
        self.filterModel.setConditions(fromDate=fromDate, toDate=toDate)
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('DateFilter.updateAspect(): Processing change of filter')
            (fromDate, toDate) = self.filterModel.getDateRange()
            # date range - need to map partial dates to real ones
            wxDate = wx.DateTime()
            if (fromDate):
                wx.DateTime.ParseDate(wxDate, fromDate.isoformat())
            self.fromDatePicker.SetValue(wxDate)
            Logger.debug('DateFilter.updateAspect(): Setting from date %s' % wxDate)
            wxDate = wx.DateTime()
            if (toDate):
                wx.DateTime.ParseDate(wxDate, toDate.isoformat())
            self.toDatePicker.SetValue(wxDate)
            Logger.debug('DateFilter.updateAspect(): Setting to date %s' % wxDate)
        else:
            Logger.error('DateFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))



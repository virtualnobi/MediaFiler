# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
from __builtin__ import classmethod
import datetime
import re
import os.path
import StringIO
import logging
import gettext
## Contributed 
import exifread
import wx
## nobi
from nobi.wxExtensions.Menu import Menu
from nobi.PartialDateTime import PartialDateTime
## Project
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.Entry import Entry
from Model.Group import Group
#from ..MediaNameHandler import MediaNameHandler
#from ..MediaClassHandler import MediaClassHandler
from Model.MediaOrganization import MediaOrganization



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
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
    _ = Translation.ugettext
def N_(message): return message



class OrganizationByDate(MediaOrganization):
    """A strategy to organize media by date.
    
    - Media is identified by year, month, day, number, and elements, all optional.
    - Media are stored in folders per year, per month, per day.
    - Elements are allowed on media names only.
    """



# Constants
    # format strings for date output
    FormatYear = '%04d'
    FormatMonth = '%02d'
    FormatYearMonth = (FormatYear + MediaOrganization.NameSeparator + FormatMonth)
    FormatDay = '%02d'
    FormatYearMonthDay = (FormatYearMonth + MediaOrganization.NameSeparator + FormatDay)
    UnknownDateName = (FormatYear % 0)
    # RE patterns to recognize dates
    YearString = r'(?:(?:' + UnknownDateName + ')|(?:(?:18|19|20)\d\d))'  # 4-digit year
#    YearString2 = r'(?:' + UnknownDateName + ')|(?:(?:18|19|20)\d\d)'  # 4-digit year
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



# Variables
# Class Methods
    @classmethod
    def constructPathForOrganization(self, **kwargs):
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
            year = int(self.UnknownDateName)
        result = (self.FormatYear % year)
        if (('month' in kwargs)
            and kwargs['month']):
            month = kwargs['month']
            result = os.path.join(result, (self.FormatYearMonth % (year, month)))
            if (('day' in kwargs)
                and kwargs['day']):
                result = os.path.join(result, 
                                      (self.FormatYearMonthDay % (year, month, kwargs['day'])),
                                      (self.FormatYearMonthDay % (year, month, kwargs['day'])))
            else:
                result = os.path.join(result, 
                                      (self.FormatYearMonth % (year, month)))
        else:
            result = os.path.join(result, (self.FormatYear % year))
        return(result)


    @classmethod
    def constructPathFromImport(self, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  # @UnusedVariable
        """
        """
        # determine date of image
        (year, month, day) = self.deriveDate(importParameters.log, sourcePath, importParameters.getPreferPathDateOverExifDate())
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)
        extension = extension.lower() 
        # determine elements
        newElements = self.ImageFilerModel.deriveElements(importParameters, 
                                                          sourcePath[:-len(extension)], 
                                                          baseLength, 
                                                          True, 
                                                          illegalElements)
        if (importParameters.getMarkAsNew()
            and (not self.NewIndicator in newElements)):
            newElements = (newElements + Entry.NameSeparator + self.NewIndicator)
        # ensure uniqueness via number
        newPath = self.constructPath(rootDir=targetDir,
                                year=year,
                                month=month,
                                day=day,
                                elements=newElements,
                                extension=extension[1:],
                                makeUnique=True)
        # rename
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
                logging.error('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % head)
                raise KeyError, ('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % head)
            group = Group(cls.ImageFilerModel, path)
            group.setParentGroup(parentGroup)
#             (year, month, day, pathRest) = cls.deriveDateFromPath(StringIO.StringIO(), path)  # @UnusedVariable
#             if (day <> None):
#                 day = None
#                 month = int(month)
#                 year = int(year)
#             elif (month <> None):
#                 month = None
#                 year = int(year)
#             elif (year <> None):
#                 year = None
#             else: 
#                 logging.error('OrganizationByDate.getGroupFromPath(): No valid date recognized in "%s"' % path)
#                 raise KeyError, ('OrganizationByDate.getGroupFromPath(): No valid date recognized in "%s"' % path)
#             parentPath = cls.constructPath(rootDir=cls.ImageFilerModel.getRootDirectory(),
#                                            day=day,
#                                            month=month,
#                                            year=year)
#             parentGroup = cls.getGroupFromPath(parentPath)
#             if (not parentGroup):
#                 logging.error('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % parentPath)
#                 raise KeyError, ('OrganizationByDate.getGroupFromPath(): Cannot create Group for "%s"' % parentPath)
#             group = Group(cls.ImageFilerModel, path)
#             group.setParentGroup(parentGroup)
#             return(group)
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
        #log.write('Ensuring existence of "%s"\n' % newDir)
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
        if ((exifDate[0] <> None)
            and (pathDate[0] <> self.UnknownDateName)
            and ((exifDate[0] <> pathDate[0])
                 or (exifDate[1] <> pathDate[1])
                 or (exifDate[2] <> pathDate[2]))):
            datesDiffer = True
        # select date
        if (preferPathDate):  # date derived from path takes precedence
            if (pathDate[0] <> self.UnknownDateName):
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
            elif (exifDate[0] <> None):
                (year, month, day) = exifDate
        else:  # date derived from EXIF takes precedence
            if (exifDate[0]):
                (year, month, day) = exifDate
            elif (pathDate[0] <> self.UnknownDateName):
                (year, month, day, dummy) = pathDate
        if (exifMoreSpecific):
            log.write('EXIF (%s) more specific than path (%s) in file "%s"\n' % (exifDate, pathDate, path))
        elif (datesDiffer):
            log.write('EXIF (%s) and path (%s) differ in file "%s"\n' % (exifDate, pathDate, path))
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
        if ((os.path.isfile(path)) 
            and (path[-4:].lower() == '.jpg')): 
            with open(path, "rb") as f:
                try:
                    exifTags = exifread.process_file(f)
                except:
                    logging.warning('OrganizationByDate.deriveDateFromFile(): cannot read EXIF data from "%s"!' % path)
                    return(None, None, None)
            if (('Model' in exifTags)
                and (exifTags['Model'] == 'MS Scanner')):
                logging.debug('OrganizationByDate.deriveDateFromFile(): Ignoring EXIF data because Model=MS Scanner')
                return(None, None, None)
            if (('Software' in exifTags)
                and (0 <= exifTags['Software'].find('Paint Shop Photo Album'))):
                logging.debug('OrganizationByDate.deriveDateFromFile(): Ignoring EXIF data because Software=Paint Shop Photo Album')
                return (None, None, None)
            for key in exifTags:
                if ('Date' in key):
                    logging.debug('OrganizationByDate.deriveDateFromFile(): Relevant EXIF tag "%s" in "%s"' % (key, path))
                    value = exifTags[key]
                    match = self.DayPattern.search(str(value))
                    if (match):
                        year = match.group(1)
                        month = match.group(3)
                        day = match.group(4)
                        if (year == self.UnknownDateName):
                            month = None
                            day = None
                        logging.debug('OrganizationByDate.deriveDateFromFile(): Recognized date (%s, %s, %s) in EXIF data of file "%s"\n' % (year, month, day, path)) 
                        return(year, month, day)
                    else:
                        logging.warning('OrganizationByDate.deriveDateFromFile(): EXIF tag %s contains illegal date %s' % (key, value))
        return(None, None, None)


    @classmethod
    def deriveDateFromPath(cls, log, path):  # @UnusedVariable
        """Determine the date of the file PATH. 
        
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
        logging.debug('OrganizationByDate.deriveDateFromPath(): Inspecting "%s"' % path)
        # search for date
        match = cls.DayPattern.search(path)
        usingReducedPattern = False
        if (match == None):
            usingReducedPattern = True
            match = cls.ReducedDayPattern.search(path)
        if (match):
            logging.debug('OrganizationByDate.deriveDateFromPath(): Day pattern matched')
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
                logging.debug('OrganizationByDate.deriveDateFromPath(): Simple day pattern matched')
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
                    logging.debug('OrganizationByDate.deriveDateFromPath(): Month pattern matched')
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
                        logging.debug('OrganizationByDate.deriveDateFromPath(): Year pattern matched')
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
        logging.debug('OrganizationByDate.deriveDateFromPath(): Recognized (%s, %s, %s) in path "%s"\n' % (year, month, day, path)) 
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
    def deriveDateFromPath2(cls, log, path):  # @UnusedVariable
        """Determine the date of a file from its path. 
        
        StringIO log is used to report progress. 
        String path contains the absolute filename.  
        Return a triple (year, month, day, rest) where 
            year, month, and day are either String or None 
            String rest contains the rest of path not consumed by the match
        """
        year = None
        month = None
        day = None
        usingReducedPattern = False
        # search for date
        match = cls.DayPattern.search(path)
        if (match == None):
            usingReducedPattern = True
            match = cls.ReducedDayPattern.search(path)
        if (match):
            year = match.group(1)
            month = match.group(3)
            day = match.group(4)
            if (usingReducedPattern):
                if (len(year) <> 2):
                    logging.error('OrganizationByDate.deriveDateFromPath(): Reduced year "%s" too long in "%s"' % (year, path)) 
                    return(cls.UnknownDateName, None, None, path)
                year = cls.expandReducedYear(year)
            matched = path[match.start():match.end()]
            matchIndex = match.start()
        else:
            usingReducedPattern = False
            match = cls.GermanDayPattern2.search(path)
            if (match == None):
                usingReducedPattern = True
                match = cls.ReducedGermanDayPattern2.search(path)
            if (match): 
                day = match.group(1)
                month = match.group(3)
                year = match.group(4)
                if (usingReducedPattern):
                    if (len(year) <> 2):
                        logging.error('OrganizationByDate.deriveDateFromPath(): Reduced year "%s" too long in "%s"' % (year, path)) 
                        return(cls.UnknownDateName, None, None, path)
                    year = cls.expandReducedYear(year)
                matched = path[match.start():match.end()]
                matchIndex = match.start()
            else:
                usingReducedPattern = False
                match = cls.MonthPattern.search(path)
                if (match == None):
                    usingReducedPattern = True
                    match = cls.ReducedMonthPattern.search(path)
                if (match):
                    year = match.group(1)
                    month = match.group(2)
                    if (usingReducedPattern):
                        if (len(year) <> 2):
                            logging.error('OrganizationByDate.deriveDateFromPath(): Reduced year "%s" too long in "%s"' % (year, path)) 
                            return(cls.UnknownDateName, None, None, path)
                        year = cls.expandReducedYear(year)
                    matched = path[match.start():match.end()]
                    matchIndex = match.start()
                else: 
                    match = cls.YearPattern.search(path)
                    if (match):
                        year = match.group(1)
                        matched = path[match.start():match.end()]
                        matchIndex = match.start()
                    else:
                        (year, month, day) = cls.deriveDateWithMonthFromPath(log, path)
                        if (year):
                            matched = ''
                            matchIndex = -1
                        else:
                            year = cls.UnknownDateName
                            matched = ''
                            matchIndex = -1
        # skip to last occurrence of match
        rest = path
        while (matchIndex >= 0):  
            rest = rest[(matchIndex + len(matched)):]
            matchIndex = rest.find(matched)
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
    def registerMoveToLocation(cls, path):
        """
        """
        print('OrganizationByDate.registerMoveToLocation(): Registering "%s"' % path)
#         (year, month, day, dummy) = cls.deriveDateFromPath(StringIO.StringIO(), path)
#         (dummy, menuText) = os.path.split(path)
#         if (not menuText in cls.MoveToLocations):
#             cls.MoveToLocations[menuText] = {'year': year, 'month': month, 'day': day}
#             if (GUIId.MaxNumberMoveToLocations < len(cls.MoveToLocations)):
#                 cls.MoveToLocations.popitem(last=False)
        


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        # year
        aMediaNamePane.yearInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(80,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.yearInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.yearInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.NameSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # month
        aMediaNamePane.monthInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.monthInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.monthInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.NameSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # day
        aMediaNamePane.dayInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.dayInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.dayInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # generic 
        MediaOrganization.initNamePane(aMediaNamePane)



# Lifecycle
# Setters
    def setIdentifiersFromPath(self, path):
        """Set year, month, day (if any) from path, and return remaining part of path.
        
        Returns a String containing the remaining part of PATH to the right of the last identifier found.
        """
        (year, month, day, rest) = self.deriveDateFromPath(StringIO.StringIO(), path)
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
    def constructPathForSelf(self, **kwargs):
        """
        """
        checkMakeUnique = False
        if (not 'year' in kwargs):
            kwargs['year'] = self.getYear()
        elif (kwargs['year'] <> self.getYear()):
            checkMakeUnique = True
        if (not 'month' in kwargs):
            kwargs['month'] = self.getMonth()
        elif(kwargs['month'] <> self.getMonth()):
            checkMakeUnique = True
        if (not 'day' in kwargs):
            kwargs['day'] = self.getDay()
        elif (kwargs['day'] <> self.getDay()):
            checkMakeUnique = True
        if (checkMakeUnique
            and (not 'number' in kwargs)):
            kwargs['makeUnique'] = True
        return(super(OrganizationByDate, self).constructPathForSelf(**kwargs))


    def extendContextMenu(self, menu):
        """Extend the context menu to contain functions relevant for organization by date.

        MediaFiler.Entry.Menu menu 
        Return nobi.wxExtensions.Menu (which is a wx.Menu)
        """
        moveToMenu = Menu()
        moveToId = GUIId.SelectMoveTo
        for mtl in sorted(self.__class__.MoveToLocations):
#             menuText = mtl
#             if (moveToId <= (GUIId.SelectMoveTo + GUIId.MaxNumberMoveToLocations)):
#                 mtl = self.__class__.MoveToLocations[menuText]
#                 print('Adding move-to location "%s" into menu entry %s with id %d' % (mtl, menuText, moveToId))
#                 moveToMenu.Append(moveToId, menuText)
#                 if ((mtl['year'] == self.getYearString())
#                     and (mtl['month'] == self.getMonthString())
#                     and (mtl['day'] == self.getDayString())):
#                     moveToMenu.Enable(moveToId, False)
            moveToMenu.Append(moveToId, mtl)
            moveToId = (moveToId + 1)
        menu.PrependMenu(0, GUIId.FunctionNames[GUIId.SelectMoveTo], moveToMenu)
        if (GUIId.SelectMoveTo == moveToId):  
            menu.Enable(0, False)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions to handle the menu items added in extendContextMenu()
        """
        if ((GUIId.SelectMoveTo <= menuId)
            and (menuId <= (GUIId.SelectMoveTo + GUIId.MaxNumberMoveToLocations))):
            mtlIndex = (menuId - GUIId.SelectMoveTo)
            print('NYI: Moving "%s" to "%s"' % (self.context.getPath(), self.__class__.MoveToLocations[mtlIndex]))
#             mtlText = sorted(self.__class__.MoveToLocations.keys())[mtlIndex]
#             mtl = self.__class__.MoveToLocations[mtlText]
#             print('Moving "%s" to %s' % (self.getPath(), mtl))
#             self.context.renameTo(makeUnique=True, **mtl)
        else:
            super(OrganizationByDate, self).runContextMenuItem(self, menuId, parentWindow)


    def getDateTaken(self):
        if (self.dateTaken == None):
            logging.error('OrganizationByDate.getDateTaken(): No date found for "%s"' % self.context.getPath())
        return(self.dateTaken)


    def getYear(self):
        if (((self.year <> None)
             and (self.dateTaken <> None)
             and (int(self.year) <> self.dateTaken.getYear()))
            or ((self.year == None)
                and self.dateTaken.getYear())):
            print('OrganizationByDate.getYear(): explicit and PartialDateTime year do not match')
        if (self.year == None):
            return(None)
        else:
            return(int(self.year))

    
    def getYearString(self):
        if (self.dateTaken
            and self.dateTaken.getYear()):
            return(self.__class__.FormatYear % self.dateTaken.getYear())
        else:
            return(self.__class__.UnknownDateName)


    def getMonth(self):
        if (((self.month <> None)
             and (self.dateTaken <> None)
             and (int(self.month) <> self.dateTaken.getMonth()))
            or ((self.month == None)
                and (self.dateTaken <> None)
                and self.dateTaken.getMonth())):
            print('OrganizationByDate.getMonth(): explicit and PartialDateTime month do not match')
        if (self.month == None):
            return(None)
        else:
            return(int(self.month))
    

    def getMonthString(self):
        if (self.dateTaken
            and self.dateTaken.getMonth()):
            return(self.__class__.FormatMonth % self.dateTaken.getMonth())
        else:
            return(u'')

    
    def getDay(self):
        if (((self.day <> None)
             and (self.dateTaken <> None)
             and (int(self.day) <> self.dateTaken.getDay()))
            or ((self.day == None)
                and (self.dateTaken <> None)
                and self.dateTaken.getDay())):
            print('OrganizationByDate.getDay(): explicit and PartialDateTime day do not match')
        if (self.day == None):
            return(None)
        else:
            return(int(self.day))    


    def getDayString(self):
        if (self.dateTaken
            and self.dateTaken.getDay()):
            return(self.__class__.FormatDay % self.dateTaken.getDay())
        else:
            return(u'')



# Other API Funcions
    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        super(OrganizationByDate, self).setValuesInNamePane(aMediaNamePane)
        aMediaNamePane.yearInput.SetValue(self.getYearString())
        aMediaNamePane.monthInput.SetValue(self.getMonthString())
        aMediaNamePane.dayInput.SetValue(self.getDayString())


    def getValuesFromNamePane(self, aMediaNamePane):
        """
        
        Return Dictionary mapping String to values
            or None if field values are illegal
        """
        result = super(OrganizationByDate, self).getValuesFromNamePane(aMediaNamePane)
        year = aMediaNamePane.yearInput.GetValue()
        if (year == ''):
            result['year'] = None
        else:
            try:
                result['year'] = int(year)
            except:
                logging.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret year string "%s" as int' % year)
                return(None)
        month = aMediaNamePane.monthInput.GetValue()
        if (month == ''):
            result['month'] = None
        else:
            try:
                result['month'] = int(month)
            except:
                logging.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret month string "%s" as int' % month)
                return(None)
        day = aMediaNamePane.dayInput.GetValue()
        if (day == ''):
            result['day'] = None
        else:
            try:
                result['day'] = int(day)
            except: 
                logging.warning('OrganizationByDate.getValuesFromNamePane(): Cannot interpret day string "%s" as int' % day)
                return(None)
        return(result)



# Event Handlers
# Internal - to change without notice

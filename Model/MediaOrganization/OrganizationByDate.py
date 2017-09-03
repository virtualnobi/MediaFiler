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
from ..Entry import Entry
#from ..Group import Group
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
    YearString = '((?:' + UnknownDateName + ')|(?:(?:18|19|20)\d\d))'  # 4-digit year
    ReducedYearString = r'[/\\](\d\d)'  # 2-digit year, only allowed at beginning of path component
    MonthString = '[01]\d'  # 2-digit month
    DayString = '[0123]\d'  # 2-digit day
    SeparatorString = r'[-_:/\.\\]'  # separator characters
    YearPattern = re.compile('%s(?!\d)' % YearString)
    ReducedYearPattern = re.compile('%s(?!\d)' % ReducedYearString)
    MonthPattern = re.compile('%s%s(%s)(?!\d)' % (YearString, SeparatorString, MonthString))
    ReducedMonthPattern = re.compile(r'%s%s(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString))
    DayPattern = re.compile('%s(%s)(%s)\\2(%s)(?!\d)' % (YearString, SeparatorString, MonthString, DayString))
    ReducedDayPattern = re.compile('%s(%s)(%s)\\2(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString, DayString))



# Variables
# Class Methods
    @classmethod
    def constructPathForOrganization(self, **kwargs):
        """
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
            result = os.path.join(result,
                                  (self.FormatYear % year))
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
        """
        """
        (year, month, day, pathRest) = cls.deriveDateFromPath(StringIO.StringIO(), path)  # @UnusedVariable
        group = cls.ImageFilerModel.getEntry(group=True, year=year, month=month, day=day)
        if (group):
            return(group)
        else:
            return(super(OrganizationByDate, cls).getGroupFromPath(path))


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
        date = None
        if ((os.path.isfile(path))  # plain file
            and (path[-4:].lower() == '.jpg')):  # of type JPG
            with open(path, "rb") as f:
                try:
                    exifTags = exifread.process_file(f)
                except:
                    logging.warning('OrganizationByDate.deriveDateFromFile(): cannot read EXIF data from "%s"!' % path)
                    return(None, None, None)
                if (('Model' in exifTags)
                    and (exifTags['Model'] == 'MS Scanner')):
                    return(None, None, None)
                if (('Software' in exifTags)
                    and (0 <= exifTags['Software'].find('Paint Shop Photo Album'))):
                    return (None, None, None)
                if (exifTags):
                    for key in ['DateTimeOriginal',
                                # 'Image DateTime',  # bad date, changed by imaging software
                                'EXIF DateTimeOriginal', 
                                'EXIF DateTimeDigitized'
                                ]:
                        if (key in exifTags):
                            date = exifTags[key]
                            break
                    if (date):
                        match = self.DayPattern.search(str(date))
                        year = match.group(1)
                        month = match.group(3)
                        day = match.group(4)
                        if (year == self.UnknownDateName):
                            month = None
                            day = None
                        #log.write('Recognized date (%s, %s, %s) in EXIF data of file "%s"\n' % (year, month, day, path)) 
                        return(year, month, day)
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
        # search for date
        match = cls.DayPattern.search(path)
        usingReducedPattern = False
        if (match == None):
            usingReducedPattern = True
            match = cls.ReducedDayPattern.search(path)
        if (match):
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
            matchIndex = match.start()
        else:
            match = cls.MonthPattern.search(path)
            usingReducedPattern = False
            if (match == None):
                #log.write('Month pattern did not match in "%s"\n' % path)
                usingReducedPattern = True
                match = cls.ReducedMonthPattern.search(path)
            if (match):
                year = match.group(1)
                if (usingReducedPattern):  # fix two-digit year
                    assert (len(year) == 2), ('Reduced year "%s" too long in "%s"' % (year, path)) 
                    year = cls.expandReducedYear(year)
                month = match.group(2)
                matched = (cls.FormatYearMonth % (int(year), int(month)))
                matchIndex = match.start()
            else: 
                match = cls.YearPattern.search(path)
                usingReducedPattern = False
# A number starting the filename may be a year or just a counter - don't interpret as year
#                 if (match == None):
#                     usingReducedPattern = True
#                     match = cls.ReducedYearPattern.search(path)
                if (match):
                    year = match.group(1)
                    if (usingReducedPattern):
                        year = cls.expandReducedYear(year)
                    matched = (cls.FormatYear % int(year))
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
        #log.write('Recognized (%s, %s, %s) in path "%s"\n' % (year, month, day, path)) 
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
    def registerMoveToLocation(cls, year=None, month=None, day=None, name=None, scene=None):
        """Store information where media was moved to, for retrieval as targets for subsequent moves.
        
        String year
        String month
        String day
        """
        if ((name <> None)
            or (scene <> None)):
            raise ValueError
        print('OrganizationByDate.registerMoveToLocation(): Registering (%s, %s, %s)' % (year, month, day))
        moveToLocation = {'year': year, 'month': month, 'day': day}
        path = cls.constructPathForOrganization(rootDir='', **moveToLocation)
        (dummy, menuText) = os.path.split(path)
        if (not menuText in cls.MoveToLocations):
            cls.MoveToLocations[menuText] = moveToLocation
            if (GUIId.MaxNumberMoveToLocations < len(cls.MoveToLocations)):
                cls.MoveToLocations.popitem(last=False)


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
        self.dateTaken = PartialDateTime(year, month, day)
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
        moveToId = GUIId.SelectMoveToLocation
        for menuText in sorted(self.__class__.MoveToLocations.keys()):
            if (moveToId <= (GUIId.SelectMoveToLocation + GUIId.MaxNumberMoveToLocations)):
                mtl = self.__class__.MoveToLocations[menuText]
                print('Adding move-to location "%s" into menu entry %s with id %d' % (mtl, menuText, moveToId))
                moveToMenu.Append(moveToId, menuText)
                if ((mtl['year'] == self.getYearString())
                    and (mtl['month'] == self.getMonthString())
                    and (mtl['day'] == self.getDayString())):
                    moveToMenu.Enable(moveToId, False)
                moveToId = (moveToId + 1)
        if (GUIId.SelectMoveToLocation < moveToId):  
            menu.AppendMenu(0, GUIId.FunctionNames[GUIId.SelectMoveToLocation], moveToMenu)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions to handle the menu items added in extendContextMenu()
        """
        if ((GUIId.SelectMoveToLocation <= menuId)
            and (menuId <= (GUIId.SelectMoveToLocation + GUIId.MaxNumberMoveToLocations))):
            mtlIndex = (menuId - GUIId.SelectMoveToLocation)
            mtlText = sorted(self.__class__.MoveToLocations.keys())[mtlIndex]
            mtl = self.__class__.MoveToLocations[mtlText]
            print('Moving "%s" to %s' % (self.getPath(), mtl))
            self.context.renameTo(makeUnique=True, **mtl)
        else:
            super(OrganizationByDate, self).runContextMenuItem(self, menuId, parentWindow)


    def getDateTaken(self):
        return(self.dateTaken)


    def getYear(self):
        if (((self.year <> None)
             and (int(self.year) <> self.dateTaken.getYear()))
            or ((self.year == None)
                and self.dateTaken.getYear())):
            print('OrganizationByDate.getYear(): explicit and PartialDateTime year do not match')
        if (self.year == None):
            return(None)
        else:
            return(int(self.year))

    
    def getYearString(self):
        if (self.dateTaken.getYear()):
            return(self.__class__.FormatYear % self.dateTaken.getYear())
        else:
            return(self.__class__.UnknownDateName)


    def getMonth(self):
        if (((self.month <> None)
             and (int(self.month) <> self.dateTaken.getMonth()))
            or ((self.month == None)
                and self.dateTaken.getMonth())):
            print('OrganizationByDate.getMonth(): explicit and PartialDateTime month do not match')
        if (self.month == None):
            return(None)
        else:
            return(int(self.month))
    

    def getMonthString(self):
        if (self.dateTaken.getMonth()):
            return(self.__class__.FormatMonth % self.dateTaken.getMonth())
        else:
            return(u'')

    
    def getDay(self):
        if (((self.day <> None)
             and (int(self.day) <> self.dateTaken.getDay()))
            or ((self.day == None)
                and self.dateTaken.getDay())):
            print('OrganizationByDate.getDay(): explicit and PartialDateTime day do not match')
        if (self.day == None):
            return(None)
        else:
            return(int(self.day))    


    def getDayString(self):
        if (self.dateTaken.getDay()):
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
                return(None)
        month = aMediaNamePane.monthInput.GetValue()
        if (month == ''):
            result['month'] = None
        else:
            try:
                result['month'] = int(month)
            except:
                return(None)
        day = aMediaNamePane.dayInput.GetValue()
        if (day == ''):
            result['day'] = None
        else:
            try:
                result['day'] = int(day)
            except: 
                return(None)
        return(result)



# Event Handlers
# Internal - to change without notice

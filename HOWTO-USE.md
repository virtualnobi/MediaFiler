# How to use MediaFiler?

## Running MediaFiler

If you completed the installation as described, you have a shortcut on your desktop which will run MediaFiler in a directory of your choice. Clicking the shortcut will open MediaFiler with a standard initial image and a default layout of panes. A "pane" is a area inside the window showing certain information. Panes can be rearranged and hidden, and the current layout of all panes can be saved as a "perspective" and restored later. 

More information on how to change the window layout can be found at wxPython.AUI. 

On the top, there is the usual main menu which offers the following groups of actions: 
* "Program" contains the export and exit functions.
* "Media" 
* "View"
* "Perspective"
* "Import"
* "Tool"

There are the following panes: 
* The canvas pane shows the media. It is the only pane which cannot be hidden. Depending on the selection, one or more media are shown in a grid layout. The context menu is available for each media. Clicking on the canvas background will change the selected media to the parent group. 
* The "Media" pane shows the media files grouped by their date. The largest groups are years, which contain groups for months, which in turn contain groups for days. Media files can be placed into any of the groups; so an image can be put into a year group if the month and day of its being taken is unknown. There is a special group "0000" to contain all media which have no date at all. 
* The "Name" pane shows the components of the media file's name: Year, month, and day (if given), a number to uniquely identify the media within its group, and a list of tags, separated by dots ("."). Each of these components may be changed manually; hit ENTER in any of the text fields or the "Rename" button to rename the media. If the date is changed, the media will be moved according to the new date. The "Last Used" button will change the media tags to those last saved from the Name pane. The "Remove Unknown" button will remove all unknown elements (i.e., those not declared to be tags) from the tag list. 
* The "Classification" pane shows the tags assigned to the selected media. Each tag class is shown as one group, with the class name as title. If the class is single-selection, a radio button group is used for the tags; if it's multiple-selection, checkboxes are used for the tags. Selecting or unselecting a tag here immediately changes the media tags (which is also shown in the Media and Name panes). 
* The "Filter" pane allows you to limit the media displayed in the Media and Canvas panes to a subset of all media. The buttons "Clear Filter" and "Use Filter" turn filtering off and on. Media can be filtered for size, date, and existence of tags. 
* The "Presentation" pane contains buttons to start and pause the presentation, show next and previous media manually, and switch the presentation duration per media. 

The pane layout can be changed by dragging the panes. The following predefined perspectives are accessible from the "Perspective" menu: 
* "Classify" contains the Media, Name, Classification and Canvas panes. 
* "Search" contains the Filter, Name, Classification and Canvas panes.
* "Present" contains the Presentation and Canvas panes. It is best used after setting up a filter, then switching to this perspective and showing the media. 
* "All Panes" shows all panes at once.
* "Last Used" changes back to the last used perspective.  

## Adding media files

You can copy the media into the folder structure created by MediaFiler directly. It will be easier, however, to use the import function. 

### Importing media

If you want to add many media files at once to MediaFiler, use the "Import" function from the menu. You can set a few parameters before importing, and will receive a log of what has been imported at the end. 

The Dialog which appears when you press "Import" contains these options: 
* The first field shows the directory from which media files will be imported. It is prefilled, either with a standard directory or with the last directory used when importing. 
* "Delete Originals" controls whether the original files will be deleted after import. Checking this will automatically clear the directory you specify in the first field. Only media files which are imported will be deleted; files which are too small or have an unknown type (see below) will not be deleted.
* "Ignore Unhandled Files" controls whether to import all files found, or only those which MediaFiler knows how to display. Currently, many image and video formats are known. 
* "Maximum Number..." specifies the maximum number of files to import. If there are more, you should check "Delete Originals" and import in several phases. This is a workaround because the log cannot be displayed for several thousands of imported media, and should be fixed. 
* "Minimum File Size" specifies the minimum size (in bytes) a media file must have to be imported. If you have thumbnails and images, you can set this to ignore the thumbnails and only import the images. 
* "Mark Imported Files..." will result in a "new" tag to be added to all imported files. After import, you may filter to see only the newly imported files, to change their classification, for example. 
* "Report Illegal Tags" will include a list of unknown (illegal) tags found in the imported media's file names in the final log window. 
* "Prefer Date..." defines which date to use if the imported media contains two dates. Images may contain their date of taking (depending on the camera); the standard is called EXIF. The media's file name may also contain a date in the form of "year-month-day" which is recognized by MediaFiler. MediaFiler usually prefers the EXIF date, but you may prefer the date from the file name by checking this option. 

"Test Import" does the same as "Import", except it does not actually move any files. It will display the log as though it did, so you can check where the imported media files would be placed. 

"Remove Import Indicator" will remove the "new" tag which was added automatically from all media in the collection. You usually do not need this function because you would filter for the media with "new" tag and remove the tag when you correct the classification. 

### MediaFiler folder structure and file names

This section is of interest only if you want to fiddle with the media files manually. 

#### images

This directory will contain subdirectories for years, which again have subdirectories for months, which again have subdirectories for days. All subdirectories on all levels may contain media files, whose pathnames begin with the same date. A year is a four-digit number, months and days are two-digit numbers, separated by a dash "-".

Media pathnames begin with the date, followed by a three-digit number, followed by the tags, followed by the file type extension.

`2000/2000-04/2000-04-01/2000-04-01-001.some.media.new.jpg` is thus a JPG image (last component `.jpg`) taken on the 1st of April in 2000, which is tagged with `some` and `media`. It also has the special tag `new` which means it has been imported automatically (and the tag has not been manually removed). 

#### lib

#### import

You may put media to import into this directory. It is used as default in the "Import" functions. 

#### trash

All media which you delete in MediaFiler will be moved here instead of a real deletion. This is a safety measure and may change in future releases.


## Using tags

"Tags" are labels assigned to the media files which allow you to find media more easily. Tags are grouped into "Classes" to formulate conditions on tag usage; for example, only one tag out of a class may be used, or a tag may only be used if a tag from another class is also used. 

In the example from above, `2000/2000-04/2000-04-01/2000-04-01-001.some.media.new.jpg`, there are three tags, `some`, `media`, and `new`. Tags are separated with a dot ".", and `new` is a special tag created when importing new media.  

### Defining tags

Currently, tags are defined in a tet file in `lib/classes.txt`. When running MediaFiler for the first time, a skeleton file with some explanations is generated at this location. Changes to this file determine how the MediaFiler window looks (see below), but they do not change any media file. Don't be afraid to experiment. 

If the `editor-text`configuration option is set correctly for your computer, you can edit this file using the "Tool>Edit Classes" function. 

### Assigning tags to media

There are three way how tags can be assigned to media: 
- when importing media, parts of the filename are converted to tags,
- in the "Classification Pane", you can assign the tags which are defined as described above, 
- in the "Name Pane", you can enter any tag.

#### Converting Pathnames into Tags during Import

#### Assigning Defined Tags in the "Classification Pane"

The tags and classes are shown in the "Classification" pane. For the media selected in the tree page, you will see the tags currently assigned, and can change this assignment by checking or unchecking tags. Changes you make here are executed immediately on the media pathname. 

If a class is single-selection, the tags in this class are shown as a radio button group, i.e., only one of them can be checked. There is an additional `none` tag to signal none of the tags should be assigned. 

If a class is multi-selection, the tags in this class are shown as a check box group, i.e., multiple of them can be checked.  

For all classes, an additional `n/a` tag is active when a group is selected, which shows that the media in the group has differing assignments.  

#### Assigning Tags in the "Name Pane"

The "Name Pane" shows fields for year, month, day as well as a number and a text field. You can enter any text in the last field. Certain characters will be interpreted as separators, such as dot ".", dash "-", or space " ". When you hit ENTER in the text field, or click the "Rename" button, the tags will be alphabetically ordered and the media file renamed. 

### Searching for media with certain tags
 
The reason to have media tagged is that you can search for them later. The "Filter Pane" shows many ways to search for media, among them all the tags defined, as well as unknown tags. 

Each tag class is shown as one row, with a selection list for the tags in the class and a filter mode selection. The filter mode can be `required` (the tag must appear), `prohibited` (the tag may not appear), `ignore` (tag is irrelevant for filtering). 

There's special entry `all` in the tags list, which will match any tag from the class. With this entry, you may search for media which has any of the tags in the class. 


## Advanced Settings

### Configuration File

A few advanced settings are available in a configuration file. The configuration is stored in the '&lt;your installation directory&gt;/lib/MediaFiler.ini' file, which is a text file you can edit with any simple text editor program. 

The following options exist: 

- `maximize-on-start = True`
If set to `True`, the program will use the whole screen when starting. If set to `False` (or not existing), the program will use a fixed size, which might not fit your screen. 

- `editor-text = "C:/Program Files (x86)/Gnu/Emacs-24.5/bin/emacs.exe" "%1"` 
The program to use when editing text files (like tags and classes). You may use whatever text editor you like. Put the `%1` where the program expects the name of the file to be edited. The quotes `"` ensure filenames with spaces work as well. 

- `viewer-image = "C:\Program Files (x86)\IrfanView\i_view32.exe" "%1" /fs`
There's a "fullscreen" action in the MediaFiler program which will run the program indicated with this option on a selected image. If you want to further edit the image, for example, use this. 

- `viewer-movie = "C:\Program Files\VideoLAN\VLC\vlc.exe" -f "%1"`
This is the program to use for the "fullscreen" action for movies. Currently, that's the only way to view movies.  

- `editor-email = "C:\Program Files (x86)\Mozilla\Thunderbird\thunderbird.exe" -compose "attachment='%1'"`
If you want to email a selected media to somebody, you can put your email program here. Don't forget the `%1` for the filename of the image (most likely, to be used as an attachment to the email). 

There are more options in this file, especially if you have used the MediaFiler program already. It's probably best to leave them unchanged, but here they are for completeness: 

- `last-perspective = 0`
The last perpective shown. "Perspective" is wxPython term to describe the layout of the window panes (media hierarchy, filter, preview, etc.).

- `last-media = N:\shared\images\images\2002\2002-08\2002-08-005.Henning.Lars.Luebeln.jpg`
The last media shown. 

- `import-prefer-exif = True`
- `import-path = N:\shared\import`
The settings used during the last import. 

The images used by the MediaFiler program can be tweaked as well. Just replace the images in the directory by ones you like better: 

- logo.ico
The icon shown on the window frame, and in the taskbar representing the program.

- initial.jpg
This image is shown when no media is selected. Usually, the program starts by showing the media shown when using the program last time, so you should not seen this often. 

- Image.jpg
- Movie.jpg
The images used to represent the media, if the media cannot be shown. For images, seeing this image means there has been an error loading the image. For movies, this image is used always. 

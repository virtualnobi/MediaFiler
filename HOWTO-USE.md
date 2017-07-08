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
* "Delete Originals" controls whether the original files will be deleted after import. Checking this will automatically clear your mobile's storage.
* "Ignore Unhandled Files" controls whether to import all files found, or only those which MediaFiler knows how to display. Currently, many image and video formats are known. 
* "Maximum Number..." specifies the maximum number of files to import. If there are more, you should check "Delete Originals" and import in several phases. This is a workaround because the log cannot be displayed for several thousands of imported media, and should be fixed. 
* "Minimum File Size" specifies the minimum size (in bytes) a media file must have to be imported. If you have thumbnails and images, you can set this to ignore the thumbnails and only import the images. 
* "Mark Imported Files..." will result in a "new" tag to be added to all imported files. After import, you may filter to see only the newly imported files, to change their classification, for example. 
* "Report Illegal Tags" will include a list of unknown (illegal) tags found in the imported media's file names in the final log window. 
* "Prefer Date..." defines which date to use if the imported media contains two dates. Images may contain (depending on the camera) their date of taking; the standard is called EXIF. The media's file name may also contain a date in the form of "year-month-day" which is recognized by MediaFiler. MediaFiler usually prefers the EXIF date, but you may prefer the date from the file name by checking this option. 

"Test Import" does the same as "Import", except it does not actually move any files. It will display the log as though it did, so you can check where the imported media files would be placed. 

"Remove Import Indicator" will remove the "new" tag which was added automatically from all media in the collection. You usually do not need this function because you would filter for the media with "new" tag and remove the tag when you correct the classification. 

### MediaFiler folder structure and file names

This section is of interest only if you want to fiddle with the media files manually. 

#### images

#### lib

#### import

#### trash

## Using tags

"Tags" are labels assigned to the media files which allow you to find media more easily. Tags are grouped into "Classes" to formulate conditions on tag usage; for example, only one tag out of a class may be used, or a tag may only be used if a tag from another class is also used. 

### Defining tags

### Assigning tags to media

### Searching for media with certain tags
 

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

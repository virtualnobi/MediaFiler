# MediaFiler
A Python 2.7 GUI app to organize media

# How to install?

## Install Python and Python Libraries

* Install Python 2.7.10 from [python.org](http://python.org/download): 
Be sure to check the 'Add to Path' option in the installer. 
I recommend 2.7.10 because it includes 'pip' (2.7.13 seems not to).

* Upgrade 'pip' with the command line 'pip install --ugrade pip': 
This might run into permissions errors on Windows. For Windows 10, type 'cmd' into the seach field, and press Ctrl+Shift+Enter (instead of only Enter) to execute the command line interpreter in administrator mode.

* Install the exifread modul with the command 'pip install exifread' 

* Install wxPython for Python 2.7 from [wxpython.org](http://wxpython.org/download.php) 

## Install the MediaFiler sources

There are two options: Either you use a Github account to download updates, or you download the sources as a ZIP file. 

### Connect to Github

* Create a Github account on []()

* Download Github Desktop from []()

* Clone the MediaFiler repository from [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler)

* More to do...

### Stand-alone Installation

If you don't want a github account, and are willing to repeat these steps for every update of the MediaFiler program:

* Go to the [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler)

* Click the 'Clone or Download' button

* Choose 'Download ZIP'

* More to do...

## Set up MediaFiler

* Set the LANGUAGE parameter to your locale. Supported values are "de_DE" and "en_US":
On Windows 10, enter 'Environment Variable' (or 'Umgebungsvariable') into the Windows search field. The program which comes up has a button 'Evironment Variables', which presents user-specific variables. Usually, LANGUAGE is not defined, so you need to press 'New'. 

* Pick or create an image directory to keep all your images:
A good choice on Windows is '/Users/<your-user-name>/Pictures/MediaFiler'. 
Mediafiler will create subdirectories called 'images' (all your images), 'lib' (some configuration files), 'trash' (all media you delete, for easy recovery), and 'import' (the default directory from which media is imported).

* Create a shortcut for the 'App.pyw' file, move it to your desktop, and change its working directory to the image directory.

* Start the shortcut.

# How to help?

* Translate if you need another language: 
This project uses the standard PO/MO translation files. You'll find them in the 'locale' folder. Just send me translated versions. 


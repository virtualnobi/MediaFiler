# How to install MediaFiler?

## Install Python and Python Libraries

* Install Python 2.7.10 from [python.org](http://python.org/download): 
Be sure to check the 'Add to Path' option in the installer. 
I recommend 2.7.10 because it includes 'pip' (2.7.13 seems not to).

* Upgrade 'pip' (the Python package manager):
Type 'cmd' into the Windows search field and run the command interpreter. Type 'pip install --ugrade pip' into its window. If you run into permissions errors on Windows, type 'cmd' into the search field, and press Ctrl+Shift+Enter (instead of only Enter) to execute the command line interpreter in administrator mode, then try the pip command again.

* Install the exifread module:
In the command interpreter, type the command 'pip install exifread'. This will install a module to read the date when a photo was taken from the image metadata.  

* Install wxPython for Python 2.7 from [wxpython.org](http://wxpython.org/download.php): 
wxPython is the GUI toolkit used by MediaFiler.  

## Install the MediaFiler sources

There are two options: Either you use a Github account to download updates, or you download the sources as a ZIP file. Using a Github account will make upgrading to a new version much easier, and will allow you to participate in further developing MediaFiler. If you use a ZIP file, you need to repeat this procedure every time you want to upgrade to a new version. 

### Connect to Github

* Create a Github account on [https://github.com/](https://github.com/).

* Download Github Desktop from [https://desktop.github.com/](https://desktop.github.com/).

* Clone the MediaFiler repository from [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler):
Note the this installation directory into for later. 

### Stand-alone Installation

* Go to the page [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler).

* Click the 'Clone or Download' button.

* Choose 'Download ZIP'.

* Extract the ZIP archive into a directory of your choice. Note this installation directory for later. 

## Set up MediaFiler

* Set the LANGUAGE variable to your locale:
On Windows 10, enter 'Environment Variable' (or 'Umgebungsvariable') into the Windows search field. The program which comes up has a button 'Evironment Variables', which presents user-specific variables. Usually, LANGUAGE is not defined, so you need to press 'New'. Enter 'LANGUAGE' and the locale you wish to use. Currently supported values are "de_DE" and "en_US". 

* Set the PYTHONPATH variable to include your installation directory: 
Following the same procedure as above, make sure an environment variable PYTHONPATH exists. (It should after the installation of Python.) This list contains a semicolon-separated list of places where Python code is searched. Add the directory where you installed MediaFiler to this list; don't forget to add the semicolon as separator.  

* Pick or create an image directory to keep all your images:
A good choice on Windows is '/Users/&tl;your-user-name&gt;/Pictures/MediaFiler'. 
Mediafiler will create subdirectories called 'images' (all your images), 'lib' (some configuration files), 'trash' (all media you delete, for easy recovery), and 'import' (the default directory from which media is imported).

* Create a shortcut for the app:
In the installation directory, there is an 'App.pyw' file. Create a shortcut to this file and move it to your desktop. In the properties for this shortcut, change the working directory (German "Ausführen In:") to the image directory you've chosen in the previous step.

* Start the shortcut.

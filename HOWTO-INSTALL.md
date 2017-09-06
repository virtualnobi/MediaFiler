# How to install MediaFiler?

The steps you need to do are similar on all operating systems (i.e. whether you use a Mac, a Linux or Windows computer). The decriptions how to complete each steps are currently for Windows 10. If you use another operating system, let me know the details and I can add them here. 

## Install Python and Python Libraries

* Install Python 2.7.10 from [python.org](http://python.org/download):
Python is the programming language used to develop the MediaFiler program.  
I recommend version 2.7.10 because it includes 'pip' (2.7.13 seems not to). Be sure to check the 'Add to Path' option in the installer. 

* Upgrade pip:
Pip is a program to download additional Python libraries. 
Type `cmd` into the Windows search field and run the command interpreter. Type `pip install --ugrade pip` into its window. If you run into permissions errors on Windows, type `cmd` into the search field, and press Ctrl+Shift+Enter (instead of only Enter) to execute the command interpreter in administrator mode, then try the pip command again.

* Install the exifread module:
The exifread Python module reads the date when a photo was taken from the image metadata.  
In the command interpreter, type the command `pip install exifread`. 

* Install wxPython for Python 2.7 from [wxpython.org](http://wxpython.org/download.php): 
wxPython is the GUI toolkit used by MediaFiler.

## Install the MediaFiler program

There are two options for you: Either you use a Github account to download updates, or you download the sources as a ZIP file. Using a Github account will make upgrading to a new version easier, and will allow you to participate in developing MediaFiler. If you use a ZIP file, you need to repeat this procedure every time you want to upgrade to a new version. 

### Stand-alone Installation Using ZIP File

* Go to the Github page [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler).

* Click the `Clone or Download` button.

* Choose `Download ZIP`.

* Extract the ZIP archive into a directory of your choice. Note this as your installation directory for later. 

### Use Github account

* Create a Github account on [https://github.com/](https://github.com/).

* Install Github Desktop from [https://desktop.github.com/](https://desktop.github.com/).

* Start Github Desktop.

* Clone the MediaFiler repository from [github.com/virtualnobi/MediaFiler](https://github.com/virtualnobi/MediaFiler).
Note the directory it is cloned into as your installation directory into for later. 

## Set up the MediaFiler program on your computer

* Set the `LANGUAGE` variable to your locale:
On Windows 10, enter 'Environment Variable' (German: 'Umgebungsvariable') into the Windows search field. The program which comes up has a button 'Evironment Variables', which presents user-specific variables. Usually, LANGUAGE is not defined, so you need to press 'New'. Enter `LANGUAGE` and the locale you wish to use. Currently supported values are `de_DE` and `en_US`. 

* Set the PYTHONPATH variable to include your installation directory: 
Following the same procedure as above, make sure an environment variable PYTHONPATH exists. (It should after the installation of Python.) This list contains a semicolon-separated list of places where Python code is searched. Add the installation directory from above to the end of this list; don't forget to add the semicolon as separator.  

* Pick or create an image directory to keep all your images:
A good choice on Windows is `/Users/&lt;your-user-name&gt;/Pictures/MediaFiler`. 

* Create a shortcut for the app:
In the installation directory, there is an `App.pyw` file. Create a shortcut to this file and move it to your desktop. In the properties for this shortcut, change the working directory (German `Ausführen In:`) to the image directory from the previous step.

* Start the shortcut:
Clicking the shortcut should run the MediaFiler program. When started for the first time, it will ask your for the image directory. If erverything is working correctly, the directory shown by default is correct, but you can still choose another one. Mediafiler will create subdirectories called `images` (all your images), `lib` (some configuration files), `trash` (all media you delete, for easy recovery), and `import` (the default directory from which media is imported).

## Congratulations! You're done with the setup. 

Continue with [https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md](https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md).

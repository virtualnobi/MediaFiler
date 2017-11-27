# How to configure MediaFiler? 


## Install External Viewers And Players

MediaFiler can display images. If you want to view movies, or want to edit images, you can install a program to do this, and configure MediaFiler so it will start this program if you want. 

### Images

If you want to be able to view (and edit) images with an external program, you can tell MediaFiler how to invoke this program. I use IrfanView, which can be downloaded from [http://www.irfanview.com/](http://www.irfanview.com/), but you may use any other image viewer or editor. 

See section Advanced Settings>Configuration File>viewer-image in [https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md](https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md) to learn how to configure an external program for viewing images.


### Videos

If you want to include videos in your media collection, they will display a generic movie icon by default. 

In case you want to see a frame from the video instead, you have to install the ffmpeg program and tell MediaFiler where to find it. You can install ffmpeg from [https://ffmpeg.org/](https://ffmpeg.org/). 

See section Advanced Settings>Configuration File>ffmpeg in [https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md](https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md) to learn how to configure MediaFiler to use ffmpeg.

In case you want to be able to view the entire video in a separate window, you have to install a video player (or use a built-in player) and tell MediaFiler where to find it. I use VLC, which can be downloaded from [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/). 

See section Advanced Settings>Configuration File>viewer-movie in [https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md](https://github.com/virtualnobi/MediaFiler/blob/master/HOWTO-USE.md) to learn how to configure an external program for viewing movies.


## Advanced Settings

### Configuration File

A few advanced settings are available in a configuration file. The configuration is stored in the '<your image directory>/lib/MediaFiler.ini' file, which is a text file you can edit with any simple text editor program. 

The following options exist: 

- `maximize-on-start = True`
If set to `True`, the program will use the whole screen when starting. If set to `False` (or not existing), the program will use a fixed size, which might not fit your screen. 

- `editor-text = "C:/Program Files (x86)/Gnu/Emacs-24.5/bin/emacs.exe" "%1"` 
The program to use when editing text files (like tags and classes). You may use whatever text editor you like. Put the `%1` where the program expects the name of the file to be edited. The quotes `"` ensure filenames with spaces work as well. 

- `viewer-image = "C:\Program Files (x86)\IrfanView\i_view32.exe" "%1" /fs`
There's a "fullscreen" action in the MediaFiler program which will run the program indicated on a selected image (with '%1' replaced by the actual image filename). If you want to further edit the image, for example, use this. 

- `viewer-movie = "C:\Program Files\VideoLAN\VLC\vlc.exe" -f "%1"`
This is the program to use for the "fullscreen" action for movies (with '%1' replaced by the actual image filename). As MediaFiler currently only shows a representative image for movies (either movie icon, or a single frame of the movie), this is the only way to view movies.  

- `ffmpeg = "C:\Program Files\ffmpeg\bin\ffmpeg.exe"`
This is the program which derives a still image from a movie. If you do not install ffmpeg, only a generic image will be shown for all videos. If you install ffmpeg, the frame at 20% of the video duration is shown for a video.

- `editor-email = "C:\Program Files (x86)\Mozilla\Thunderbird\thunderbird.exe" -compose "attachment='%1'"`
If you want to email a selected media to somebody, you can put your email program here. Don't forget the `%1` for the filename of the image (most likely, to be used as an attachment to the email). 

- `show-parent-after-remove = True`
Controls which item is selected in the tree view after deleting media. If `True`, the parent group is shown. As this might cause a long delay to display all entries in the group, and you might loose the orientation which media is the next or previous, you can leave this option out or set it to "False" to show the previous media after deleting one. 

There are more options in this file, especially if you have used the MediaFiler program already. It's probably best to leave them unchanged, but here they are for completeness: 

- `last-perspective = 0`
The last perspective shown. "Perspective" is wxPython term to describe the layout of the window panes (media hierarchy, filter, preview, etc.).

- `last-media = C:\your\installation\directory\2000\2000-04\2000-04-01\2000-04-01-001.set.of.tags.for.your.jpg`
The last media shown. 

- `import-prefer-exif = True`
- `import-path = N:\shared\import` plus many more...
The settings used during the last import. 


### Standard Images

The images used by the MediaFiler program can be tweaked as well. Just replace the images in the `lib` directory by ones you like better: 

- logo.ico:
The icon shown on the window frame, and in the taskbar representing the program.

- initial.jpg:
This image is shown when no media is selected. Usually, the program starts by showing the media shown when using the program last time, so you should not seen this often. 

- Image.jpg
- Movie.jpg:
The images used to represent the media, if the media cannot be shown. For images, seeing this image means there has been an error loading the image. For movies, this image is used if you did not install ffmpeg and configure MediaFiler to use it (see section Configuration File>ffmpeg). 

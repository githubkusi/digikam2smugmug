# digikam2smugmug
This project integrates [digiKam](https://www.digikam.org/), a great open source photo management tool, with [Smugmug](https://www.smugmug.com/), a feature rich photo cloud storage. DigiKam allows you to organize, tag and rate your photos. digikam2smugmug is a uni-directional sync service which uploadas your photos including tags/ratings/comments from DigiKam to Smugmug
## Motivation
While DigiKam is a great photo management software, it lacks a cloud based front end which allows you to access your photos via web browser or mobile. Smugmug (in contrast to other platforms such as Google Photo) allows to preserve tags/comments/ratings from DigiKam. DigiKam's internal Smugmug uploader does not support a sync service which keeps Smugmug up-to-date with DigiKam's database.

## Features
* Uni-directional sync from DigiKam to Smugmug
* Keep Smugmug in sync with your DigiKam database with one single command
* Configurable upload logic based on file-/folder name/ratings/tags
* Keep upload history in DigiKam db
* Sync metadata changes in DigiKam of already uploaded photos, (tags/ratings/comments)

## Installation
Recommended installation with [pipx](https://pypa.github.io/pipx/), but of course all other standard Python installation methods will do

    pipx install .

Create a file ~/.digikam2smugmug containing

    smugmug:
      api_key: "Pkasd434nh..."
      api_secret: "mj438xD4D..."
      token: "232jkfixBVCSE..."
      secret: "3dfems..."

    digikam:
      user: "<your username>"
      password: "<your pass>"
      database: "<core digikam tablename>"
      digikamnode: "<root level foldername in Smugmug, eg Digikam>"  

Resolve to https://github.com/adhawkins/smugmugv2py and https://api.smugmug.com/api/v2/doc for the Smugmug authentication

## DigiKam SQL database

### Requirements
* DigiKam needs to be run with a mysql database backend
* mysql_config, provided by package libmariadb-devel (Opensuse)
* Installation of mysqlclient needs gcc, python38-devel 
* Recommended: https://dbeaver.io

### New table
Create new table `PhotoSharing`
|Key| Description |
|--|--|
| `imageid` | Foreign Key to Images.ID (e.g 326490) |
|`remoteid` | SmugmugID (e.g /api/v2/album/dpgRrc/image/9SjdbR5-0)
| `mtime_metadata` | Timestamp of metadata on Smugmug. Currently, this includes rating, tags, title and caption

### Alter existing tables
- Add column `mtime` to `ImageTags`        : updated when tag is set (seemingly it is also updated on changing the rating)
- Add column  `mtime` to `ImageInformation` : updated when rating is set
- Add column  `mtime` to `ImageComments`    : updated when title or caption is set

### Convert stock digikam sql db
Do the above steps automatically with the scripts `create-photosharing.sql` and `add-timestamp.sql`. Needlesss to say: do database backups before you run the scripts!

    mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/create-photosharing.sql
    mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/add-timestamp.sql

## Upload filter
You can configure the upload behavior with the file `.smugmug-config`, located at the root of your photo library

    [exclude path]
    # Relative path to folder or image
    /my/event
    /my/event/photo.jpg

    [exclude tags]
    # Files are uploaded without the specified tag
    private_tag_1
    private_tag_2
    
    [exclude files with tags]
    # Files containing the tag are  not uploaded
    private_tag_3
    
    [minimal rating]
    # <album path> : <rating between 0 and 5>
    
	# Minimal default rating for upload
    DEFAULT : 1

    # Minimal 2 stars for photos in folder /my/event
    /my/event : 2



## Issues
* `smugmugv2py` uses [rauth](https://github.com/litl/rauth) for authentication, whose upstream seems inactive by now. This PRQ is needed to make rauth work with python3. [This fork](https://github.com/githubkusi/rauth) contains said PRQ
* This tool is being used since 2018. So far, each version of DigiKam was compatible with the altered db setup. However this is not guaranteed to work with future versions. Whenever you update your DigiKam installation, make sure you backup your db
* Deleting albums is not yet fully implemented. Albums need to be deleted manually on Smugmug. Check the script `src/delete-album-from-photosharing.sql` to delete traces of Smugmug in the DigiKam Core db

## Credits
All the hard work of accessing Smugmug was done by Andy Hawkins with his great tool https://github.com/adhawkins/smugmugv2py. `digikam2smugmug` is basically a fork of his tool, extended with DigiKam functionality and a Python3 port.

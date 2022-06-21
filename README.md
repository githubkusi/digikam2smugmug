# smugv2py
Python library for the SmugMug v2 API

## Installation

    pipx install .

Create a file ~/.digikam2smugmug containing

    smugmug:
      api_key: "Pkzb4cpnh..."
      api_secret: "mZc83xD4D..."
      token: "2jTmZfCbnxBVZXKfC..."
      secret: "38WfsXWnhV..."

    digikam:
      user: "user"
      password: "pass"
      database: "digikam tablename"
      digikamnode: "Digikam"


## Python 3 caveats

You need to apply this PRQ https://github.com/litl/rauth/pull/201 to rauth in order to make rauth work with python3    


# Digikamdb
## Requirements
mysql_config, provided by package libmariadb-devel

Installation of mysqlclient needs gcc, python38-devel 


## New table PhotoSharing
- imageid:          Foreign Key to Images.ID (e.g 326490)
- remoteid:         SmugmugID (e.g /api/v2/album/dpgRrc/image/9SjdbR5-0)
- mtime\_metadata:  Timestamp of metadata on Smugmug. Currently, this includes rating, tags, title and caption

## Alter existing tables
- Add column mtime to ImageTags        : updated when tag is set (seemingly it is also updated on changing the rating)
- Add column mtime to ImageInformation : updated when rating is set
- Add column mtime to ImageComments    : updated when title or caption is set

## Convert stock digikam sql db
mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/create-photosharing.sql
mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/add-timestamp.sql






